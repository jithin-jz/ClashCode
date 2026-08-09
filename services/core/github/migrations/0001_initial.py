import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GitHubConnection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("github_username", models.CharField(max_length=255)),
                (
                    "access_token_encrypted",
                    models.BinaryField(help_text="AES-256-GCM encrypted GitHub OAuth token"),
                ),
                (
                    "repo_name",
                    models.CharField(
                        default="clashcode-solutions",
                        help_text="Target repository name (created if not exists)",
                        max_length=100,
                    ),
                ),
                (
                    "repo_visibility",
                    models.CharField(
                        choices=[("public", "Public"), ("private", "Private")],
                        default="public",
                        help_text="Whether the solutions repo should be public or private",
                        max_length=10,
                    ),
                ),
                (
                    "is_enabled",
                    models.BooleanField(
                        default=True,
                        help_text="Master switch — user can pause sync without disconnecting",
                    ),
                ),
                (
                    "include_problem_description",
                    models.BooleanField(
                        default=True,
                        help_text="Include the full problem statement in the README",
                    ),
                ),
                ("last_sync_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True, default="")),
                (
                    "consecutive_failures",
                    models.IntegerField(
                        default=0,
                        help_text="Auto-disable after N consecutive failures",
                    ),
                ),
                ("total_pushes", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="github_connection",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "GitHub Connection",
                "verbose_name_plural": "GitHub Connections",
            },
        ),
        migrations.CreateModel(
            name="GitHubPushLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("challenge_title", models.CharField(max_length=255)),
                ("challenge_slug", models.CharField(max_length=255)),
                ("challenge_order", models.IntegerField(default=0)),
                (
                    "challenge_description",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Problem statement for the README (stored at push time)",
                    ),
                ),
                ("user_code", models.TextField()),
                ("language", models.CharField(default="python", max_length=20)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("IN_PROGRESS", "In Progress"),
                            ("SUCCESS", "Success"),
                            ("FAILED", "Failed"),
                            ("SKIPPED", "Skipped"),
                        ],
                        default="PENDING",
                        max_length=15,
                    ),
                ),
                ("commit_sha", models.CharField(blank=True, default="", max_length=40)),
                ("commit_url", models.URLField(blank=True, default="")),
                ("error_message", models.TextField(blank=True, default="")),
                ("retry_count", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("pushed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "duration_ms",
                    models.IntegerField(
                        blank=True,
                        help_text="Total time from task start to completion in ms",
                        null=True,
                    ),
                ),
                (
                    "connection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="push_logs",
                        to="github.githubconnection",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["connection", "-created_at"],
                        name="github_conn_created_idx",
                    ),
                    models.Index(
                        fields=["status"],
                        name="github_status_idx",
                    ),
                    models.Index(
                        fields=["connection", "challenge_slug"],
                        name="github_conn_slug_idx",
                    ),
                ],
            },
        ),
    ]
