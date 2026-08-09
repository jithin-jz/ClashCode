from django.contrib import admin

from .models import GitHubConnection, GitHubPushLog
from .tasks import push_solution_to_github


@admin.register(GitHubConnection)
class GitHubConnectionAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "github_username",
        "repo_name",
        "repo_visibility",
        "is_enabled",
        "consecutive_failures",
        "total_pushes",
        "last_sync_at",
    ]
    list_filter = ["is_enabled", "repo_visibility", "consecutive_failures"]
    search_fields = ["user__username", "github_username"]
    readonly_fields = ["created_at", "updated_at", "last_sync_at", "total_pushes", "consecutive_failures"]

    # NEVER expose the encrypted token in admin
    exclude = ["access_token_encrypted"]

    actions = ["reset_failures", "disable_connections", "enable_connections", "retry_all_failed"]

    @admin.action(description="✓ Reset failure counters")
    def reset_failures(self, request, queryset):
        updated = queryset.update(consecutive_failures=0, last_error="")
        self.message_user(request, f"Reset failure counters for {updated} connection(s).")

    @admin.action(description="✗ Disable selected connections")
    def disable_connections(self, request, queryset):
        updated = queryset.update(is_enabled=False)
        self.message_user(request, f"Disabled {updated} connection(s).")

    @admin.action(description="✓ Enable selected connections")
    def enable_connections(self, request, queryset):
        updated = queryset.update(is_enabled=True, consecutive_failures=0, last_error="")
        self.message_user(request, f"Enabled {updated} connection(s) and reset their failures.")

    @admin.action(description="🔄 Retry ALL failed pushes for selected users")
    def retry_all_failed(self, request, queryset):
        """
        Bulk-retry: Re-queue all FAILED push logs for the selected connections.
        Resets their status to PENDING and fires the Celery task.
        """
        total_retried = 0

        for connection in queryset.filter(is_enabled=True):
            failed_logs = GitHubPushLog.objects.filter(
                connection=connection,
                status=GitHubPushLog.Status.FAILED,
            )

            log_ids = list(failed_logs.values_list("id", flat=True))

            if log_ids:
                # Batch update status
                failed_logs.update(
                    status=GitHubPushLog.Status.PENDING,
                    error_message="",
                )

                # Queue each for async processing
                for log_id in log_ids:
                    push_solution_to_github.delay(log_id)

                total_retried += len(log_ids)

        if total_retried:
            self.message_user(
                request,
                f"🔄 Re-queued {total_retried} failed push(es) for retry.",
            )
        else:
            self.message_user(
                request,
                "No failed pushes found for the selected connections (or connections are disabled).",
                level="WARNING",
            )


@admin.register(GitHubPushLog)
class GitHubPushLogAdmin(admin.ModelAdmin):
    list_display = [
        "get_username",
        "challenge_title",
        "language",
        "status",
        "duration_display",
        "retry_count",
        "created_at",
        "pushed_at",
    ]
    list_filter = ["status", "language", "created_at"]
    search_fields = ["challenge_title", "challenge_slug", "connection__user__username"]
    readonly_fields = [
        "connection",
        "challenge_title",
        "challenge_slug",
        "challenge_order",
        "commit_sha",
        "commit_url",
        "created_at",
        "started_at",
        "pushed_at",
        "duration_ms",
    ]
    date_hierarchy = "created_at"

    # Don't show full code in admin list
    exclude = ["user_code", "challenge_description"]

    actions = ["retry_selected", "mark_as_skipped"]

    @admin.display(description="User", ordering="connection__user__username")
    def get_username(self, obj):
        return obj.connection.user.username

    @admin.display(description="Duration")
    def duration_display(self, obj):
        if obj.duration_ms is None:
            return "—"
        if obj.duration_ms < 1000:
            return f"{obj.duration_ms}ms"
        return f"{obj.duration_ms / 1000:.1f}s"

    @admin.action(description="🔄 Retry selected pushes")
    def retry_selected(self, request, queryset):
        """Retry selected push logs."""
        retried = 0
        for log in queryset.exclude(status=GitHubPushLog.Status.SUCCESS):
            if log.connection.is_enabled:
                log.status = GitHubPushLog.Status.PENDING
                log.error_message = ""
                log.save(update_fields=["status", "error_message"])
                push_solution_to_github.delay(log.id)
                retried += 1

        self.message_user(request, f"Re-queued {retried} push(es).")

    @admin.action(description="⏭ Mark as skipped (won't retry)")
    def mark_as_skipped(self, request, queryset):
        """Mark logs as skipped — permanently stops retry."""
        updated = queryset.exclude(status=GitHubPushLog.Status.SUCCESS).update(status=GitHubPushLog.Status.SKIPPED)
        self.message_user(request, f"Marked {updated} push(es) as skipped.")
