"""
Prometheus metrics exporter for GitHub Sync.

Exposes counters and histograms that Prometheus scrapes via ServiceMonitor.
Grafana dashboards query these metrics for the monitoring panel.

Metrics exposed:
- github_sync_pushes_total (counter) — by status, user
- github_sync_push_duration_seconds (histogram) — latency distribution
- github_sync_connections_total (gauge) — active vs disabled
- github_sync_failures_total (counter) — by error type
- github_sync_rate_limit_remaining (gauge) — current rate limit budget
"""

import logging

from django.db.models import Avg, Count
from django.utils import timezone

from .models import GitHubConnection, GitHubPushLog

logger = logging.getLogger(__name__)

# ─── Metric Storage (In-Memory Counters for Prometheus Pull) ─────────────
# In production with multiple workers, these would use prometheus_client library.
# For CLASHCODE's architecture (analytics service proxies Prometheus), we expose
# metrics via a /metrics endpoint that the ServiceMonitor scrapes.


class GitHubSyncMetrics:
    """
    Collects and exposes GitHub sync metrics.

    Two modes:
    1. Real-time: In-memory counters updated by task callbacks
    2. Aggregated: DB-computed stats for dashboard display

    The analytics service fetches aggregated stats via internal API.
    """

    # ─── Aggregated Stats (DB-computed, for dashboards) ──────────────

    @staticmethod
    def get_dashboard_metrics(time_window_hours: int = 24) -> dict:
        """
        Compute dashboard metrics for the last N hours.
        Called by the admin analytics endpoint.
        """
        since = timezone.now() - timezone.timedelta(hours=time_window_hours)

        logs = GitHubPushLog.objects.filter(created_at__gte=since)
        connections = GitHubConnection.objects.all()

        # Push counts by status
        status_counts = logs.values("status").annotate(count=Count("id")).order_by()
        status_map = {item["status"]: item["count"] for item in status_counts}

        total = sum(status_map.values())
        success = status_map.get("SUCCESS", 0)
        failed = status_map.get("FAILED", 0)

        # Duration stats (only successful pushes)
        duration_stats = logs.filter(
            status=GitHubPushLog.Status.SUCCESS,
            duration_ms__isnull=False,
        ).aggregate(
            avg_ms=Avg("duration_ms"),
        )

        # Percentile approximation via ordering
        successful_logs = logs.filter(
            status=GitHubPushLog.Status.SUCCESS,
            duration_ms__isnull=False,
        ).order_by("duration_ms")

        p95_ms = None
        count = successful_logs.count()
        if count > 0:
            p95_index = int(count * 0.95)
            p95_log = successful_logs[min(p95_index, count - 1)]
            p95_ms = p95_log.duration_ms

        # Connection health
        active_connections = connections.filter(is_enabled=True).count()
        disabled_connections = connections.filter(is_enabled=False).count()
        unhealthy_connections = connections.filter(is_enabled=True, consecutive_failures__gte=3).count()

        # Error breakdown
        error_breakdown = (
            logs.filter(status=GitHubPushLog.Status.FAILED)
            .values("error_message")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        # Top failing users
        top_failures = (
            logs.filter(status=GitHubPushLog.Status.FAILED)
            .values("connection__user__username")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # Hourly push rate (last 24h)
        hourly_buckets = []
        for i in range(min(time_window_hours, 24)):
            bucket_start = since + timezone.timedelta(hours=i)
            bucket_end = bucket_start + timezone.timedelta(hours=1)
            bucket_count = logs.filter(
                created_at__gte=bucket_start,
                created_at__lt=bucket_end,
                status=GitHubPushLog.Status.SUCCESS,
            ).count()
            hourly_buckets.append(
                {
                    "hour": bucket_start.strftime("%H:%M"),
                    "count": bucket_count,
                }
            )

        return {
            "time_window_hours": time_window_hours,
            "pushes": {
                "total": total,
                "success": success,
                "failed": failed,
                "pending": status_map.get("PENDING", 0) + status_map.get("IN_PROGRESS", 0),
                "skipped": status_map.get("SKIPPED", 0),
                "success_rate": round((success / total) * 100, 1) if total > 0 else 0,
            },
            "latency": {
                "avg_ms": round(duration_stats["avg_ms"]) if duration_stats["avg_ms"] else None,
                "p95_ms": p95_ms,
            },
            "connections": {
                "total": active_connections + disabled_connections,
                "active": active_connections,
                "disabled": disabled_connections,
                "unhealthy": unhealthy_connections,
            },
            "errors": {
                "top_errors": [{"message": e["error_message"][:100], "count": e["count"]} for e in error_breakdown],
                "top_failing_users": [
                    {"username": u["connection__user__username"], "failures": u["count"]} for u in top_failures
                ],
            },
            "hourly_rate": hourly_buckets,
        }

    # ─── Prometheus Text Format Export ───────────────────────────────

    @staticmethod
    def prometheus_export() -> str:
        """
        Export metrics in Prometheus text exposition format.
        Scraped by Prometheus via ServiceMonitor.
        """
        connections = GitHubConnection.objects.all()
        active = connections.filter(is_enabled=True).count()
        disabled = connections.filter(is_enabled=False).count()

        # Last hour stats for rate metrics
        last_hour = timezone.now() - timezone.timedelta(hours=1)
        recent_logs = GitHubPushLog.objects.filter(created_at__gte=last_hour)

        success_count = recent_logs.filter(status=GitHubPushLog.Status.SUCCESS).count()
        failed_count = recent_logs.filter(status=GitHubPushLog.Status.FAILED).count()
        pending_count = recent_logs.filter(
            status__in=[GitHubPushLog.Status.PENDING, GitHubPushLog.Status.IN_PROGRESS]
        ).count()

        # Avg duration
        avg_duration = (
            recent_logs.filter(
                status=GitHubPushLog.Status.SUCCESS,
                duration_ms__isnull=False,
            ).aggregate(
                avg=Avg("duration_ms")
            )["avg"]
            or 0
        )

        lines = [
            "# HELP github_sync_connections_active Number of active GitHub connections",
            "# TYPE github_sync_connections_active gauge",
            f"github_sync_connections_active {active}",
            "",
            "# HELP github_sync_connections_disabled Number of disabled GitHub connections",
            "# TYPE github_sync_connections_disabled gauge",
            f"github_sync_connections_disabled {disabled}",
            "",
            "# HELP github_sync_pushes_total Total pushes in last hour by status",
            "# TYPE github_sync_pushes_total gauge",
            f'github_sync_pushes_total{{status="success"}} {success_count}',
            f'github_sync_pushes_total{{status="failed"}} {failed_count}',
            f'github_sync_pushes_total{{status="pending"}} {pending_count}',
            "",
            "# HELP github_sync_push_duration_avg_ms Average push duration in ms (last hour)",
            "# TYPE github_sync_push_duration_avg_ms gauge",
            f"github_sync_push_duration_avg_ms {round(avg_duration)}",
            "",
        ]

        return "\n".join(lines) + "\n"
