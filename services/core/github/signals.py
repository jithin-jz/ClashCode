"""
Signal handler: Triggers GitHub push on challenge completion.

Design:
- Code is stored DIRECTLY in GitHubPushLog (not in ephemeral cache)
- Signal reads from cache but the cache is just a transport mechanism
  with the PushLog as the durable record
- Problem description is captured at push time (immutable snapshot)
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from challenges.models import UserProgress

from .models import GitHubConnection, GitHubPushLog
from .tasks import push_solution_to_github

logger = logging.getLogger(__name__)


@receiver(post_save, sender=UserProgress)
def trigger_github_sync_on_completion(sender, instance, **kwargs):
    """
    Queue a GitHub push when a challenge is completed.
    Coexists with other UserProgress signals (certificates, leaderboard).
    """
    _ = sender, kwargs

    if instance.status != UserProgress.Status.COMPLETED:
        return

    user = instance.user
    challenge = instance.challenge

    # Check for active connection
    try:
        connection = GitHubConnection.objects.get(user=user, is_enabled=True)
    except GitHubConnection.DoesNotExist:
        return

    # Deduplicate: skip if already successfully pushed
    if GitHubPushLog.objects.filter(
        connection=connection,
        challenge_slug=challenge.slug,
        status=GitHubPushLog.Status.SUCCESS,
    ).exists():
        return

    # Get the user's submitted code from cache
    from django.core.cache import cache

    cache_key = f"github_sync:last_code:{user.id}:{challenge.id}"
    user_code = cache.get(cache_key, "")

    if not user_code:
        logger.warning(f"No cached code for {user.username}/{challenge.slug}. " f"GitHub push skipped.")
        return

    cache.delete(cache_key)

    # Detect language from code or default
    language = _detect_language(user_code, challenge)

    # Create the durable push record (code lives here, not in cache)
    push_log = GitHubPushLog.objects.create(
        connection=connection,
        challenge_title=challenge.title,
        challenge_slug=challenge.slug,
        challenge_order=challenge.order,
        challenge_description=challenge.description or "",
        user_code=user_code,
        language=language,
    )

    # Fire async task
    push_solution_to_github.delay(push_log.id)

    logger.info(f"Queued GitHub push: {user.username}/{challenge.title} (log={push_log.id})")


def _detect_language(code: str, challenge) -> str:
    """
    Detect programming language from code content.
    Extend this as you add multi-language support.
    """
    # Check for obvious language markers
    indicators = {
        "javascript": ["const ", "let ", "var ", "function ", "console.log", "=>"],
        "typescript": ["interface ", ": string", ": number", "type "],
        "java": ["public class ", "System.out", "public static void main"],
        "cpp": ["#include", "std::", "cout", "int main("],
        "go": ["package main", "func main(", "fmt."],
        "rust": ["fn main()", "println!", "let mut"],
    }

    for lang, markers in indicators.items():
        if any(marker in code for marker in markers):
            return lang

    # Default to python (primary language for CLASHCODE)
    return "python"
