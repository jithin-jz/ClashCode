"""
Main sync orchestrator — the public API that tasks call.
"""

from ..models import GitHubConnection, GitHubPushLog
from .content_builder import ContentBuilder, language_extension
from .github_client import GitHubAPIClient
from .repo_service import RepoService


class GitHubSyncService:
    """
    High-level orchestrator for pushing solutions to GitHub.
    Composes GitHubAPIClient, RepoService, and ContentBuilder.
    """

    def __init__(self, connection: GitHubConnection):
        self.connection = connection
        self.client = GitHubAPIClient(connection)
        self.repo = RepoService(self.client)
        self.content = ContentBuilder(connection)

    def push_solution(self, push_log: GitHubPushLog) -> dict:
        """
        Push a challenge solution as a single atomic commit.
        Returns dict with 'sha' and 'url'.
        """
        repo_full_name = self.repo.ensure_repo_exists()

        folder = f"level-{push_log.challenge_order:02d}-{push_log.challenge_slug}"
        ext = language_extension(push_log.language)

        files = {
            f"{folder}/solution.{ext}": push_log.user_code,
            f"{folder}/README.md": self.content.problem_readme(push_log),
        }

        return self.repo.create_tree_commit(
            repo=repo_full_name,
            files=files,
            message=f"✅ Level {push_log.challenge_order}: {push_log.challenge_title}",
        )

    def update_progress_tracker(self, repo_full_name: str = None):
        """Rebuild PROGRESS.md with current completion data."""
        if not repo_full_name:
            repo_full_name = f"{self.connection.github_username}/{self.connection.repo_name}"

        logs = GitHubPushLog.objects.filter(
            connection=self.connection,
            status=GitHubPushLog.Status.SUCCESS,
        ).order_by("challenge_order")

        content = self.content.progress_tracker(logs)

        self.client.create_or_update_file(
            repo=repo_full_name,
            path="PROGRESS.md",
            content=content,
            message="📊 Update progress tracker",
        )

    def verify_token(self) -> dict:
        """Verify stored token is valid. Returns GitHub user info."""
        resp = self.client.request("GET", "/user")
        return resp.json()

    def check_rate_limit(self) -> dict:
        """Check remaining API rate limit."""
        resp = self.client.request("GET", "/rate_limit")
        return resp.json().get("rate", {})
