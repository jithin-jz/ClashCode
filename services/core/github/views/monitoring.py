"""
Monitoring views — Prometheus metrics export and admin dashboard.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.authentication import JWTAuthentication


class GitHubMetricsView(APIView):
    """
    GET /api/github-sync/metrics/

    Prometheus-compatible metrics endpoint.
    No auth (scraped by ServiceMonitor inside cluster).
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        from django.http import HttpResponse

        from ..metrics import GitHubSyncMetrics

        content = GitHubSyncMetrics.prometheus_export()
        return HttpResponse(content, content_type="text/plain; version=0.0.4; charset=utf-8")


class GitHubDashboardMetricsView(APIView):
    """
    GET /api/github-sync/dashboard/metrics/

    Admin-only aggregated metrics for Grafana/admin dashboard.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        hours = min(int(request.query_params.get("hours", 24)), 168)

        from ..metrics import GitHubSyncMetrics

        metrics = GitHubSyncMetrics.get_dashboard_metrics(time_window_hours=hours)
        return Response(metrics)
