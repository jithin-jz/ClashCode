from datetime import timedelta

from challenges.models import Challenge, UserProgress
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import TruncDay
from django.utils import timezone
from store.models import StoreItem
from users.models import UserProfile

from administration.models import AdminAuditLog, AdminNote, AdminReport
from administration.utils import _analytics_cache_key

ANALYTICS_CACHE_TTL = 60 * 2  # 2 minutes


class AnalyticsService:
    @staticmethod
    def get_admin_dashboard_stats(request=None):
        """Retrieves top-level statistics for the admin dashboard."""
        cache_key = _analytics_cache_key("stats", request)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        total_users = User.objects.count()
        yesterday = timezone.now() - timedelta(days=1)
        active_sessions = User.objects.filter(last_login__gte=yesterday).count()
        oauth_logins = UserProfile.objects.exclude(provider__in=["email", "local"]).count()
        total_xp = UserProfile.objects.aggregate(total_xp=Sum("xp"))["total_xp"] or 0

        data = {
            "total_users": total_users,
            "active_sessions": active_sessions,
            "oauth_logins": oauth_logins,
            "total_gems": total_xp,
        }
        cache.set(cache_key, data, timeout=ANALYTICS_CACHE_TTL)
        return data

    @staticmethod
    def get_challenge_analytics(request=None):
        """Retrieves detailed challenge performance analytics."""
        cache_key = _analytics_cache_key("challenge-analytics", request)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        challenges = Challenge.objects.all()
        progress_summary = UserProgress.objects.values("challenge_id").annotate(
            total_attempts=Count("id"),
            completions=Count("id", filter=Q(status=UserProgress.Status.COMPLETED)),
            unlocked=Count("id", filter=Q(status=UserProgress.Status.UNLOCKED)),
            avg_stars=Avg("stars", filter=Q(status=UserProgress.Status.COMPLETED)),
            avg_duration=Avg(
                ExpressionWrapper(
                    F("completed_at") - F("started_at"),
                    output_field=DurationField(),
                ),
                filter=Q(
                    status=UserProgress.Status.COMPLETED,
                    started_at__isnull=False,
                    completed_at__isnull=False,
                ),
            ),
        )

        summary_by_challenge = {item["challenge_id"]: item for item in progress_summary}
        results = []
        for c in challenges:
            stat = summary_by_challenge.get(c.id, {})
            total_attempts = stat.get("total_attempts", 0)
            completions = stat.get("completions", 0)
            unlocked = stat.get("unlocked", 0)
            avg_stars = stat.get("avg_stars") or 0.0
            avg_duration = stat.get("avg_duration")
            avg_seconds = avg_duration.total_seconds() if avg_duration else 0.0
            abandoned = max(unlocked - completions, 0)

            results.append(
                {
                    "id": c.id,
                    "title": c.title,
                    "attempts": total_attempts,
                    "completions": completions,
                    "completion_rate": ((completions / total_attempts * 100) if total_attempts > 0 else 0.0),
                    "abandonment_rate": ((abandoned / total_attempts * 100) if total_attempts > 0 else 0.0),
                    "average_time_seconds": avg_seconds,
                    "avg_stars": avg_stars,
                    "is_personalized": c.created_for_user is not None,
                }
            )

        cache.set(cache_key, results, timeout=ANALYTICS_CACHE_TTL)
        return results

    @staticmethod
    def get_store_analytics(request=None):
        """Retrieves store economy and item popularity."""
        cache_key = _analytics_cache_key("store-analytics", request)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        items = StoreItem.objects.annotate(purchase_count=Count("purchases")).order_by("-purchase_count")

        item_stats = []
        for item in items:
            item_stats.append(
                {
                    "name": item.name,
                    "category": item.category,
                    "cost": item.cost,
                    "sales": item.purchase_count,
                    "revenue": item.purchase_count * item.cost,
                }
            )

        total_revenue = sum(item["revenue"] for item in item_stats)
        data = {"items": item_stats, "total_xp_spent": total_revenue}
        cache.set(cache_key, data, timeout=ANALYTICS_CACHE_TTL)
        return data

    @staticmethod
    def get_user_engagement_analytics(request=None):
        """Retrieves user engagement and growth analytics."""
        cache_key = _analytics_cache_key("user-engagement", request)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        # 1. Daily Growth
        growth_qs = (
            User.objects.filter(date_joined__gte=thirty_days_ago)
            .annotate(day=TruncDay("date_joined"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        daily_growth = [{"date": item["day"].strftime("%Y-%m-%d"), "count": item["count"]} for item in growth_qs]

        # 2. Active Users (last 24h)
        active_24h = User.objects.filter(last_login__gte=now - timedelta(days=1)).count()

        # 3. Auth Provider Distribution
        auth_dist_qs = UserProfile.objects.values("provider").annotate(count=Count("user_id"))
        auth_distribution = [{"provider": item["provider"] or "email", "count": item["count"]} for item in auth_dist_qs]

        # 4. Top Users by XP
        top_profiles = (
            UserProfile.objects.select_related("user")
            .annotate(followers_count=Count("user__followers", distinct=True))
            .order_by("-xp")[:10]
        )
        top_users = [
            {
                "username": p.user.username,
                "xp": p.xp,
                "followers": p.followers_count,
            }
            for p in top_profiles
        ]

        data = {
            "daily_growth": daily_growth,
            "active_users_24h": active_24h,
            "auth_distribution": auth_distribution,
            "top_users": top_users,
        }
        cache.set(cache_key, data, timeout=ANALYTICS_CACHE_TTL)
        return data

    @staticmethod
    def get_ultimate_analytics(request=None):
        """Unified command center analytics."""
        cache_key = _analytics_cache_key("ultimate", request)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        now = timezone.now()
        thirty_ago = now - timedelta(days=30)

        # 1. Overview Stats
        total_users = User.objects.count()
        overview = {
            "total_users": total_users,
            "active_24h": User.objects.filter(last_login__gte=now - timedelta(days=1)).count(),
            "total_challenges": Challenge.objects.count(),
            "store_catalog": StoreItem.objects.filter(is_active=True).count(),
        }

        # 2. Growth Trends
        growth_qs = (
            User.objects.filter(date_joined__gte=thirty_ago)
            .annotate(day=TruncDay("date_joined"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        growth_map = {item["day"].date(): item["count"] for item in growth_qs}
        growth_trends = []
        for i in range(31):
            day = (thirty_ago + timedelta(days=i)).date()
            if day > now.date():
                break
            growth_trends.append({"date": day.strftime("%Y-%m-%d"), "count": growth_map.get(day, 0)})

        # 3. Economy Pulse
        total_circulation_xp = UserProfile.objects.aggregate(total=Sum("xp"))["total"] or 0
        store_items = StoreItem.objects.annotate(sales=Count("purchases"))
        total_revenue = sum(item.sales * item.cost for item in store_items)
        economy_pulse = {
            "total_circulation_xp": total_circulation_xp,
            "total_store_revenue": total_revenue,
            "avg_xp_per_user": ((total_circulation_xp / total_users) if total_users > 0 else 0),
        }

        # 4. Top Challenges
        progress_summary = (
            UserProgress.objects.values("challenge_id")
            .annotate(
                attempts=Count("id"),
                completions=Count("id", filter=Q(status=UserProgress.Status.COMPLETED)),
                unlocked=Count("id", filter=Q(status=UserProgress.Status.UNLOCKED)),
                avg_stars=Avg("stars", filter=Q(status=UserProgress.Status.COMPLETED)),
                avg_duration=Avg(
                    ExpressionWrapper(
                        F("completed_at") - F("started_at"),
                        output_field=DurationField(),
                    ),
                    filter=Q(
                        status=UserProgress.Status.COMPLETED,
                        started_at__isnull=False,
                        completed_at__isnull=False,
                    ),
                ),
            )
            .order_by("-completions")[:5]
        )
        c_ids = [row["challenge_id"] for row in progress_summary]
        challenges_titles = {c.id: c.title for c in Challenge.objects.filter(id__in=c_ids)}
        top_challenges = [
            {
                "title": challenges_titles.get(row["challenge_id"], "Unknown"),
                "attempts": row["attempts"],
                "completions": row["completions"],
                "abandonment_rate": (
                    (max((row["unlocked"] or 0) - row["completions"], 0) / row["attempts"] * 100) if row["attempts"] > 0 else 0
                ),
                "average_time_seconds": (row["avg_duration"].total_seconds() if row.get("avg_duration") else 0),
                "avg_stars": row["avg_stars"] or 0,
            }
            for row in progress_summary
        ]

        # 5. Top Items
        item_stats = [{"name": item.name, "revenue": item.sales * item.cost, "sales": item.sales} for item in store_items]
        top_items = sorted(item_stats, key=lambda x: x["revenue"], reverse=True)[:5]

        # 6. Community Leaders
        top_profiles = (
            UserProfile.objects.select_related("user")
            .annotate(followers_count=Count("user__followers", distinct=True))
            .order_by("-xp")[:10]
        )
        community_leaders = [{"username": p.user.username, "xp": p.xp, "followers": p.followers_count} for p in top_profiles]

        # 7. System Health
        last_broadcast = (
            AdminAuditLog.objects.filter(action="SEND_GLOBAL_NOTIFICATION")
            .order_by("-timestamp")
            .values_list("timestamp", flat=True)
            .first()
        )
        system_health = {
            "database": "online",
            "audit_pipeline": "active",
            "open_reports": AdminReport.objects.exclude(status=AdminReport.Status.RESOLVED).count(),
            "pinned_notes": AdminNote.objects.filter(is_pinned=True).count(),
            "featured_store_items": StoreItem.objects.filter(featured=True).count(),
            "last_broadcast_at": last_broadcast.isoformat() if last_broadcast else None,
        }

        data = {
            "overview": overview,
            "growth_trends": growth_trends,
            "economy_pulse": economy_pulse,
            "top_challenges": top_challenges,
            "top_items": top_items,
            "community_leaders": community_leaders,
            "system_health": system_health,
        }
        cache.set(cache_key, data, timeout=ANALYTICS_CACHE_TTL)
        return data
