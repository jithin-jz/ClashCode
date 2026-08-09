"""
Low-level GitHub API client with rate limit awareness.
"""

import base64

import requests

from ..encryption import decrypt_token
from ..models import GitHubConnection
from .base import (
    GITHUB_API,
    RATE_LIMIT_BUFFER,
    REQUEST_TIMEOUT,
    GitHubRateLimitError,
    GitHubSyncError,
    GitHubTokenExpiredError,
    logger,
)


class GitHubAPIClient:
    """
    Thin HTTP layer over the GitHub REST API.
    Handles auth, timeouts, rate limits, and error translation.
    """

    def __init__(self, connection: GitHubConnection):
        self.connection = connection
        self._token = None

    @property
    def token(self) -> str:
        if self._token is None:
            self._token = decrypt_token(bytes(self.connection.access_token_encrypted))
        return self._token

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make an authenticated GitHub API request."""
        url = f"{GITHUB_API}{path}" if path.startswith("/") else path
        kwargs.setdefault("headers", self.headers)
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)

        resp = requests.request(method, url, **kwargs)

        # Check rate limit
        remaining = int(resp.headers.get("X-RateLimit-Remaining", "999"))
        if remaining < RATE_LIMIT_BUFFER and resp.status_code < 400:
            reset_at = int(resp.headers.get("X-RateLimit-Reset", "0"))
            logger.warning(
                f"GitHub rate limit low: {remaining} remaining. "
                f"Resets at {reset_at}. User: {self.connection.github_username}"
            )

        if resp.status_code >= 400:
            self._handle_error(resp)

        return resp

    def get_file_sha(self, repo: str, path: str) -> str | None:
        """Get SHA of an existing file, or None if not found."""
        resp = requests.get(
            f"{GITHUB_API}/repos/{repo}/contents/{path}",
            headers=self.headers,
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            return resp.json().get("sha")
        return None

    def create_or_update_file(self, repo: str, path: str, content: str, message: str) -> str:
        """Create or update a single file via the Contents API. Returns blob SHA."""
        url = f"/repos/{repo}/contents/{path}"
        existing_sha = self.get_file_sha(repo, path)

        payload = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "committer": {"name": "CLASHCODE", "email": "bot@clashcode.com"},
        }
        if existing_sha:
            payload["sha"] = existing_sha

        resp = self.request("PUT", url, json=payload)
        return resp.json().get("content", {}).get("sha", "")

    def _handle_error(self, resp: requests.Response):
        """Translate HTTP errors to our exception types."""
        if resp.status_code == 401:
            raise GitHubTokenExpiredError("GitHub token revoked or expired")

        if resp.status_code == 403:
            remaining = resp.headers.get("X-RateLimit-Remaining", "1")
            if remaining == "0":
                reset_at = int(resp.headers.get("X-RateLimit-Reset", "0"))
                raise GitHubRateLimitError(f"Rate limit exhausted. Resets at: {reset_at}", reset_at=reset_at)
            raise GitHubSyncError(f"Forbidden: {resp.text[:200]}")

        if resp.status_code == 404:
            raise GitHubSyncError(f"Not found: {resp.url}")

        if resp.status_code == 422:
            raise GitHubSyncError(f"Validation error: {resp.text[:200]}")

        raise GitHubSyncError(f"API error {resp.status_code}: {resp.text[:200]}")
