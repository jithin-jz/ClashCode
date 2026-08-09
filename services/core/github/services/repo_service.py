"""
Repository management — create, ensure exists, Git Trees API batch commits.
"""

import requests
from django.utils import timezone

from ..models import GitHubConnection
from .base import GITHUB_API, REQUEST_TIMEOUT
from .github_client import GitHubAPIClient


class RepoService:
    """Handles repo creation and Git Trees API batch commits."""

    def __init__(self, client: GitHubAPIClient):
        self.client = client
        self.connection = client.connection

    def ensure_repo_exists(self) -> str:
        """Ensure target repo exists. Create if not. Returns full name."""
        full_name = f"{self.connection.github_username}/{self.connection.repo_name}"

        resp = requests.get(
            f"{GITHUB_API}/repos/{full_name}",
            headers=self.client.headers,
            timeout=REQUEST_TIMEOUT,
        )

        if resp.status_code == 200:
            return full_name
        if resp.status_code == 404:
            return self._create_repo()

        self.client._handle_error(resp)
        return full_name

    def create_tree_commit(self, repo: str, files: dict, message: str) -> dict:
        """
        Create a single commit with multiple files using Git Trees API.
        One commit, one event, clean history.
        """
        # 1. Get HEAD
        ref_resp = self.client.request("GET", f"/repos/{repo}/git/ref/heads/main")
        head_sha = ref_resp.json()["object"]["sha"]

        # 2. Get base tree
        commit_resp = self.client.request("GET", f"/repos/{repo}/git/commits/{head_sha}")
        base_tree_sha = commit_resp.json()["tree"]["sha"]

        # 3. Create blobs
        tree_items = []
        for path, content in files.items():
            blob_resp = self.client.request(
                "POST",
                f"/repos/{repo}/git/blobs",
                json={"content": content, "encoding": "utf-8"},
            )
            tree_items.append(
                {
                    "path": path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_resp.json()["sha"],
                }
            )

        # 4. Create tree
        tree_resp = self.client.request(
            "POST",
            f"/repos/{repo}/git/trees",
            json={"base_tree": base_tree_sha, "tree": tree_items},
        )
        new_tree_sha = tree_resp.json()["sha"]

        # 5. Create commit
        commit_resp = self.client.request(
            "POST",
            f"/repos/{repo}/git/commits",
            json={
                "message": message,
                "tree": new_tree_sha,
                "parents": [head_sha],
                "author": {
                    "name": "CLASHCODE",
                    "email": "bot@clashcode.com",
                    "date": timezone.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
            },
        )
        new_commit_sha = commit_resp.json()["sha"]

        # 6. Update ref
        self.client.request(
            "PATCH",
            f"/repos/{repo}/git/refs/heads/main",
            json={"sha": new_commit_sha},
        )

        return {
            "sha": new_commit_sha,
            "html_url": f"https://github.com/{repo}/commit/{new_commit_sha}",
        }

    def _create_repo(self) -> str:
        """Create the solutions repository with professional setup."""
        from .content_builder import ContentBuilder

        is_private = self.connection.repo_visibility == GitHubConnection.RepoVisibility.PRIVATE
        username = self.connection.github_username

        payload = {
            "name": self.connection.repo_name,
            "description": f"⚡ Coding challenge solutions by @{username} — auto-synced from CLASHCODE",
            "homepage": "https://clashcode.com",
            "private": is_private,
            "auto_init": True,
            "has_issues": False,
            "has_projects": False,
            "has_wiki": False,
        }

        resp = self.client.request("POST", "/user/repos", json=payload)
        repo_data = resp.json()
        full_name = repo_data["full_name"]

        # Initialize with professional README
        builder = ContentBuilder(self.connection)
        self.client.create_or_update_file(
            repo=full_name,
            path="README.md",
            content=builder.repo_readme(),
            message="🎮 Initialize CLASHCODE solutions repo",
        )

        return full_name
