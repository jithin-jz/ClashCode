from django.urls import path

from .views import (
    GitHubConnectionView,
    GitHubConnectView,
    GitHubDashboardMetricsView,
    GitHubMetricsView,
    GitHubOAuthURLView,
    GitHubPushHistoryView,
    GitHubRetryPushView,
    GitHubSyncStatsView,
    GitHubVerifyView,
)
from .webhooks import GitHubWebhookView

urlpatterns = [
    # User-facing OAuth & connection management
    path("connect/url/", GitHubOAuthURLView.as_view(), name="github-sync-oauth-url"),
    path("connect/", GitHubConnectView.as_view(), name="github-sync-connect"),
    path("connection/", GitHubConnectionView.as_view(), name="github-sync-connection"),
    # Push history & stats
    path("history/", GitHubPushHistoryView.as_view(), name="github-sync-history"),
    path("stats/", GitHubSyncStatsView.as_view(), name="github-sync-stats"),
    path("retry/<int:log_id>/", GitHubRetryPushView.as_view(), name="github-sync-retry"),
    path("verify/", GitHubVerifyView.as_view(), name="github-sync-verify"),
    # Monitoring & observability
    path("metrics/", GitHubMetricsView.as_view(), name="github-sync-metrics"),
    path("dashboard/metrics/", GitHubDashboardMetricsView.as_view(), name="github-sync-dashboard-metrics"),
    # GitHub webhook (external, no auth — verified via HMAC signature)
    path("webhook/", GitHubWebhookView.as_view(), name="github-sync-webhook"),
]
