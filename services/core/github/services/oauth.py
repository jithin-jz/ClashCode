"""
OAuth helpers — token exchange and URL generation.
"""

import requests
from django.conf import settings

from .base import REQUEST_TIMEOUT


def get_github_oauth_url(state: str = "") -> str:
    """Build GitHub OAuth URL for the repo-sync feature."""
    from urllib.parse import urlencode

    params = {
        "client_id": settings.GITHUB_SYNC_CLIENT_ID,
        "redirect_uri": f"{settings.FRONTEND_URL}/settings/github/callback",
        "scope": "repo",
        "state": state,
    }
    return f"https://github.com/login/oauth/authorize?{urlencode(params)}"


def exchange_github_code(code: str) -> dict:
    """Exchange OAuth authorization code for an access token."""
    resp = requests.post(
        "https://github.com/login/oauth/access_token",
        json={
            "client_id": settings.GITHUB_SYNC_CLIENT_ID,
            "client_secret": settings.GITHUB_SYNC_CLIENT_SECRET,
            "code": code,
        },
        headers={"Accept": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()
