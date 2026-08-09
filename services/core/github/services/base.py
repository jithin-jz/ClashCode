"""
GitHub Sync exceptions and shared constants.
"""

import logging

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
REQUEST_TIMEOUT = (5, 15)  # (connect, read) in seconds
RATE_LIMIT_BUFFER = 50


# ─── Exceptions ──────────────────────────────────────────────────────────


class GitHubSyncError(Exception):
    """Base exception for GitHub sync operations."""

    pass


class GitHubTokenExpiredError(GitHubSyncError):
    """Token revoked or expired — cannot recover without re-auth."""

    pass


class GitHubRateLimitError(GitHubSyncError):
    """Rate limit exhausted — retry after reset."""

    def __init__(self, message: str, reset_at: int = 0):
        super().__init__(message)
        self.reset_at = reset_at
