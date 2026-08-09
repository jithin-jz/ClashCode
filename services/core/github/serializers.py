from rest_framework import serializers

from .models import GitHubConnection, GitHubPushLog


class GitHubConnectSerializer(serializers.Serializer):
    """Input: exchange OAuth code for connection."""

    code = serializers.CharField(help_text="OAuth authorization code from GitHub callback")


class GitHubConnectionSerializer(serializers.ModelSerializer):
    """Output: current connection status (never exposes token)."""

    class Meta:
        model = GitHubConnection
        fields = [
            "id",
            "github_username",
            "repo_name",
            "repo_visibility",
            "is_enabled",
            "include_problem_description",
            "last_sync_at",
            "last_error",
            "consecutive_failures",
            "total_pushes",
            "created_at",
        ]
        read_only_fields = fields


class GitHubConnectionUpdateSerializer(serializers.Serializer):
    """Input: update connection settings."""

    is_enabled = serializers.BooleanField(required=False)
    repo_name = serializers.CharField(max_length=100, required=False)
    repo_visibility = serializers.ChoiceField(
        choices=GitHubConnection.RepoVisibility.choices,
        required=False,
    )
    include_problem_description = serializers.BooleanField(required=False)

    def validate_repo_name(self, value):
        """GitHub repo name validation — strict rules."""
        import re

        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$", value):
            raise serializers.ValidationError(
                "Must start with a letter/number and contain only letters, numbers, hyphens, dots, underscores."
            )
        if value.endswith(".git"):
            raise serializers.ValidationError("Cannot end with .git")
        if ".." in value:
            raise serializers.ValidationError("Cannot contain consecutive dots.")
        if len(value) > 100:
            raise serializers.ValidationError("Must be under 100 characters.")
        return value


class GitHubPushLogSerializer(serializers.ModelSerializer):
    """Output: push history entry."""

    class Meta:
        model = GitHubPushLog
        fields = [
            "id",
            "challenge_title",
            "challenge_slug",
            "challenge_order",
            "language",
            "status",
            "commit_sha",
            "commit_url",
            "error_message",
            "retry_count",
            "duration_ms",
            "created_at",
            "pushed_at",
        ]
        read_only_fields = fields


class GitHubOAuthURLSerializer(serializers.Serializer):
    """Output: OAuth URL to redirect user to."""

    url = serializers.URLField()


class GitHubSyncStatsSerializer(serializers.Serializer):
    """Output: aggregated sync statistics."""

    total_pushes = serializers.IntegerField()
    success_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    avg_duration_ms = serializers.IntegerField(allow_null=True)
    last_push_at = serializers.DateTimeField(allow_null=True)
