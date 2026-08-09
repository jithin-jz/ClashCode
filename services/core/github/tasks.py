"""
Celery tasks for GitHub sync.

Production design:
- All GitHub I/O is async (never in request cycle)
- Exponential backoff with jitter
- Task locking to prevent duplicate runs
- Duration tracking for observability
- Circuit breaker pattern on the connection model
- PROGRESS.md update is a separate, batched task
"""

import logging
import time

from celery import shared_task
from django.core.cache import cache
from django.utils import timezone

from .models import GitHubConnection, GitHubPushLog
from .services import (
    GitHubRateLimitError,
    GitHubSyncError,
    GitHubSyncService,
    GitHubTokenExpiredError,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 4
RETRY_BACKOFF = 30


@shared_task(
    bind=True,
    max_retries=MAX_RETRIES,
    default_retry_delay=RETRY_BACKOFF,
    autoretry_for=(GitHubRateLimitError,),
    retry_backoff=True,
    retry_backoff_max=1800,
    acks_late=True,
    reject_on_worker_lost=True,
)
def push_solution_to_github(self, push_log_id: int):
    """
    Push a single solution to GitHub.
    Idempotent — safe to retry.
    """
    # ─── Task lock: prevent duplicate execution ──────────────────────
    lock_key = f"github:push_lock:{push_log_id}"
    if not cache.add(lock_key, "1", timeout=300):
        logger.info(f"Push {push_log_id} already in progress. Skipping duplicate.")
        return

    try:
        push_log = GitHubPushLog.objects.select_related("connection", "connection__user").get(id=push_log_id)
    except GitHubPushLog.DoesNotExist:
        logger.error(f"GitHubPushLog {push_log_id} not found. Aborting.")
        cache.delete(lock_key)
        return

    connection = push_log.connection

    # Skip if disabled
    if not connection.is_enabled:
        push_log.status = GitHubPushLog.Status.SKIPPED
        push_log.error_message = "Sync disabled by user"
        push_log.save(update_fields=["status", "error_message"])
        cache.delete(lock_key)
        return

    # Mark as in progress
    push_log.status = GitHubPushLog.Status.IN_PROGRESS
    push_log.started_at = timezone.now()
    push_log.save(update_fields=["status", "started_at"])

    service = GitHubSyncService(connection)
    start_time = time.monotonic()

    try:
        result = service.push_solution(push_log)

        # Success
        duration_ms = int((time.monotonic() - start_time) * 1000)
        push_log.status = GitHubPushLog.Status.SUCCESS
        push_log.commit_sha = result.get("sha", "")[:40]
        push_log.commit_url = result.get("url", "")[:200]
        push_log.pushed_at = timezone.now()
        push_log.duration_ms = duration_ms
        push_log.error_message = ""
        push_log.save(update_fields=["status", "commit_sha", "commit_url", "pushed_at", "duration_ms", "error_message"])

        # Update connection stats
        connection.record_success()

        logger.info(
            f"✓ GitHub push: {connection.user.username}/{push_log.challenge_slug} "
            f"({duration_ms}ms, SHA: {result.get('sha', '')[:7]})"
        )

        # Queue progress tracker update (debounced)
        _schedule_progress_update(connection.id)

    except GitHubTokenExpiredError as e:
        push_log.status = GitHubPushLog.Status.FAILED
        push_log.error_message = str(e)
        push_log.duration_ms = int((time.monotonic() - start_time) * 1000)
        push_log.save(update_fields=["status", "error_message", "duration_ms"])

        # Token is dead — disable immediately (not via circuit breaker)
        connection.is_enabled = False
        connection.last_error = "Token expired or revoked. Please reconnect GitHub."
        connection.save(update_fields=["is_enabled", "last_error"])

        logger.warning(f"✗ Token expired for {connection.user.username}. Connection disabled.")

        # Notify user via WebSocket if available
        _notify_user_sync_failed(connection.user.id, "Your GitHub token has expired. Please reconnect.")

    except GitHubRateLimitError as e:
        push_log.retry_count += 1
        push_log.error_message = str(e)
        push_log.status = GitHubPushLog.Status.PENDING  # Back to pending for retry
        push_log.save(update_fields=["retry_count", "error_message", "status"])

        logger.warning(f"⏳ Rate limited for {connection.user.username}. Will retry.")

        # Calculate retry delay based on reset time
        retry_delay = max(RETRY_BACKOFF, e.reset_at - int(time.time())) if e.reset_at else RETRY_BACKOFF
        cache.delete(lock_key)
        raise self.retry(exc=e, countdown=retry_delay) from e

    except GitHubSyncError as e:
        push_log.retry_count += 1
        push_log.error_message = str(e)
        push_log.duration_ms = int((time.monotonic() - start_time) * 1000)

        if self.request.retries >= MAX_RETRIES:
            push_log.status = GitHubPushLog.Status.FAILED
            push_log.save(update_fields=["status", "retry_count", "error_message", "duration_ms"])

            # Record failure on connection (may auto-disable)
            was_disabled = connection.record_failure(str(e))
            if was_disabled:
                _notify_user_sync_failed(
                    connection.user.id, "GitHub sync auto-disabled after repeated failures. Check your settings."
                )

            logger.error(f"✗ Permanent failure for {connection.user.username}/{push_log.challenge_slug}: {e}")
        else:
            push_log.status = GitHubPushLog.Status.PENDING
            push_log.save(update_fields=["status", "retry_count", "error_message", "duration_ms"])
            cache.delete(lock_key)
            raise self.retry(exc=e, countdown=RETRY_BACKOFF * (2**self.request.retries)) from e

    except Exception as e:
        push_log.status = GitHubPushLog.Status.FAILED
        push_log.error_message = f"Unexpected: {str(e)[:300]}"
        push_log.duration_ms = int((time.monotonic() - start_time) * 1000)
        push_log.save(update_fields=["status", "error_message", "duration_ms"])

        connection.record_failure(str(e))
        logger.exception(f"✗ Unexpected error for {connection.user.username}: {e}")

    finally:
        cache.delete(lock_key)


@shared_task
def update_progress_tracker(connection_id: int):
    """
    Rebuild PROGRESS.md for a connection.
    Debounced — if multiple pushes happen quickly, only one update runs.
    """
    try:
        connection = GitHubConnection.objects.get(id=connection_id, is_enabled=True)
    except GitHubConnection.DoesNotExist:
        return

    service = GitHubSyncService(connection)
    try:
        service.update_progress_tracker()
    except GitHubSyncError as e:
        logger.warning(f"Failed to update progress tracker for {connection.user.username}: {e}")


@shared_task
def retry_failed_pushes():
    """
    Periodic task: retry FAILED pushes that haven't exceeded max retries.
    Runs hourly via Celery Beat.
    """
    failed_logs = GitHubPushLog.objects.filter(
        status=GitHubPushLog.Status.FAILED,
        retry_count__lt=MAX_RETRIES,
        connection__is_enabled=True,
    ).values_list("id", flat=True)[:50]

    count = 0
    for log_id in failed_logs:
        push_solution_to_github.delay(log_id)
        count += 1

    if count:
        logger.info(f"Re-queued {count} failed GitHub pushes for retry.")


# ─── Internal Helpers ────────────────────────────────────────────────────


def _schedule_progress_update(connection_id: int):
    """
    Debounce progress tracker updates.
    If multiple pushes happen within 60s, only one update task fires.
    """
    debounce_key = f"github:progress_debounce:{connection_id}"
    if cache.add(debounce_key, "1", timeout=60):
        # Schedule with a delay so it runs after the debounce window
        update_progress_tracker.apply_async(
            args=[connection_id],
            countdown=65,  # Run 5s after debounce window closes
        )


def _notify_user_sync_failed(user_id: int, message: str):
    """
    Notify user about sync failure via the existing notification system.
    Non-critical — failures here are silently logged.
    """
    try:
        from notifications.services import NotificationService

        NotificationService.create_notification(
            user_id=user_id,
            title="GitHub Sync Issue",
            message=message,
            notification_type="system",
        )
    except Exception as e:
        logger.debug(f"Could not send GitHub sync notification: {e}")
