"""
GitHub Sync Views package.

Split for maintainability:
- oauth.py        → OAuth URL + code exchange (connect flow)
- connection.py   → Connection CRUD (get/update/delete)
- push_views.py   → History, stats, retry, verify
- monitoring.py   → Prometheus metrics + admin dashboard
"""

from .connection import GitHubConnectionView
from .monitoring import GitHubDashboardMetricsView, GitHubMetricsView
from .oauth import GitHubConnectView, GitHubOAuthURLView
from .push_views import (
    GitHubPushHistoryView,
    GitHubRetryPushView,
    GitHubSyncStatsView,
    GitHubVerifyView,
)

__all__ = [
    "GitHubOAuthURLView",
    "GitHubConnectView",
    "GitHubConnectionView",
    "GitHubPushHistoryView",
    "GitHubSyncStatsView",
    "GitHubRetryPushView",
    "GitHubVerifyView",
    "GitHubMetricsView",
    "GitHubDashboardMetricsView",
]
