from django.contrib.auth.models import User
from django.db import models


class GitHubConnection(models.Model):
    """
    Stores a user's GitHub OAuth connection for the auto-push feature.

    Separate from the authentication OAuth flow because:
    1. Different OAuth scope (repo contents vs user:email)
    2. Different lifecycle (user can disconnect sync without losing their login)
    3. Clean separation of concerns
    """

    class RepoVisibility(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="github_connection",
    )
    github_username = models.CharField(max_length=255)
    # Token encrypted at application layer before storage
    access_token_encrypted = models.BinaryField(help_text="AES-256-GCM encrypted GitHub OAuth token")
    repo_name = models.CharField(
        max_length=100,
        default="clashcode-solutions",
        help_text="Target repository name (created if not exists)",
    )
    repo_visibility = models.CharField(
        max_length=10,
        choices=RepoVisibility.choices,
        default=RepoVisibility.PUBLIC,
        help_text="Whether the solutions repo should be public or private",
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Master switch — user can pause sync without disconnecting",
    )
    include_problem_description = models.BooleanField(
        default=True,
        help_text="Include the full problem statement in the README",
    )
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    consecutive_failures = models.IntegerField(
        default=0,
        help_text="Auto-disable after N consecutive failures",
    )
    total_pushes = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "GitHub Connection"
        verbose_name_plural = "GitHub Connections"

    def __str__(self):
        status = "✓" if self.is_enabled else "✗"
        return f"[{status}] {self.user.username} → {self.github_username}/{self.repo_name}"

    # ─── Auto-disable circuit breaker ────────────────────────────────

    AUTO_DISABLE_THRESHOLD = 5

    def record_success(self):
        """Reset failure counter on successful push."""
        self.consecutive_failures = 0
        self.last_error = ""
        self.last_sync_at = models.functions.Now()
        self.total_pushes = models.F("total_pushes") + 1
        self.save(update_fields=["consecutive_failures", "last_error", "last_sync_at", "total_pushes"])

    def record_failure(self, error_msg: str):
        """Increment failure counter. Auto-disable if threshold exceeded."""
        self.consecutive_failures = models.F("consecutive_failures") + 1
        self.last_error = error_msg[:500]
        self.save(update_fields=["consecutive_failures", "last_error"])

        # Refresh to get actual value after F() expression
        self.refresh_from_db(fields=["consecutive_failures"])

        if self.consecutive_failures >= self.AUTO_DISABLE_THRESHOLD:
            self.is_enabled = False
            self.last_error = (
                f"Auto-disabled after {self.AUTO_DISABLE_THRESHOLD} consecutive failures. Last: {error_msg[:200]}"
            )
            self.save(update_fields=["is_enabled", "last_error"])
            return True  # Was disabled
        return False


class GitHubPushLog(models.Model):
    """
    Audit trail for every push attempt.

    This is the SOURCE OF TRUTH for the user's code — not a cache.
    The code is persisted here before the async task runs.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        SKIPPED = "SKIPPED", "Skipped"

    connection = models.ForeignKey(
        GitHubConnection,
        on_delete=models.CASCADE,
        related_name="push_logs",
    )
    # Challenge metadata (denormalized for independence from challenge model)
    challenge_title = models.CharField(max_length=255)
    challenge_slug = models.CharField(max_length=255)
    challenge_order = models.IntegerField(default=0)
    challenge_description = models.TextField(
        blank=True,
        default="",
        help_text="Problem statement for the README (stored at push time)",
    )

    # The actual solution
    user_code = models.TextField()
    language = models.CharField(max_length=20, default="python")

    # Push state
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
    )
    commit_sha = models.CharField(max_length=40, blank=True, default="")
    commit_url = models.URLField(blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    retry_count = models.IntegerField(default=0)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    pushed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Total time from task start to completion in ms",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["connection", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["connection", "challenge_slug"]),
        ]

    def __str__(self):
        return f"{self.connection.user.username}/{self.challenge_slug} [{self.status}]"
