"""
GitHub Sync Services package.

Split for maintainability:
- base.py           → Exceptions, constants
- github_client.py  → Low-level GitHub API HTTP client
- repo_service.py   → Repository management + Git Trees API
- content_builder.py → README/PROGRESS markdown generation
- oauth.py          → OAuth URL + token exchange
- sync_service.py   → High-level orchestrator (public API)
"""

from .base import (
    GitHubRateLimitError,
    GitHubSyncError,
    GitHubTokenExpiredError,
)
from .content_builder import ContentBuilder, language_extension
from .github_client import GitHubAPIClient
from .oauth import exchange_github_code, get_github_oauth_url
from .repo_service import RepoService
from .sync_service import GitHubSyncService

__all__ = [
    # Exceptions
    "GitHubSyncError",
    "GitHubTokenExpiredError",
    "GitHubRateLimitError",
    # Services
    "GitHubSyncService",
    "GitHubAPIClient",
    "RepoService",
    "ContentBuilder",
    # Helpers
    "get_github_oauth_url",
    "exchange_github_code",
    "language_extension",
]
