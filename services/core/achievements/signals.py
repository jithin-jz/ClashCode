"""
Achievement auto-unlock signals.

Listens for challenge completions, streak check-ins, and social actions
to automatically award achievements when conditions are met.
"""

import logging

from challenges.models import UserProgress
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from rewards.models import DailyCheckIn
from users.models import UserFollow

from .services import AchievementService

logger = logging.getLogger(__name__)


# Store original status before save
@receiver(pre_save, sender=UserProgress)
def cache_original_status(sender, instance, **kwargs):
    """Cache the original status before saving to detect changes."""
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None  # New record


# ──── Challenge-based achievements ────


@receiver(post_save, sender=UserProgress)
def check_challenge_achievements(sender, instance, created, **kwargs):
    """
    Check and unlock achievements when a challenge is completed.
    Only triggers on NEW completions, not on updates to existing completions.
    """
    # Check if this is a new completion:
    # 1. New record created with COMPLETED status, OR
    # 2. Status changed from non-COMPLETED to COMPLETED
    is_new_completion = False

    if created and instance.status == "COMPLETED":
        is_new_completion = True
        logger.info(f"New challenge completion detected for user {instance.user.username}")
    elif not created and instance.status == "COMPLETED":
        # Status changed to COMPLETED
        if getattr(instance, "_old_status", None) != "COMPLETED":
            is_new_completion = True
            logger.info(f"Challenge status changed to COMPLETED for user {instance.user.username}")

    if not is_new_completion:
        return

    user = instance.user

    # Calculate current progress
    completed_count = UserProgress.objects.filter(user=user, status="COMPLETED").count()

    logger.info(f"Challenge achievements check for {user.username}: total_completed={completed_count}")

    # Update progress for tier achievements
    # These will only unlock when completed_count >= target_value
    AchievementService.update_progress(user, "first-blood", completed_count)
    AchievementService.update_progress(user, "rising-coder", completed_count)
    AchievementService.update_progress(user, "challenge-veteran", completed_count)
    AchievementService.update_progress(user, "legend", completed_count)

    # One-off conditions
    if instance.started_at and instance.completed_at:
        elapsed = (instance.completed_at - instance.started_at).total_seconds()
        if elapsed < 120:
            logger.info(f"Speed condition met for {user.username}: completed in {elapsed:.1f}s (< 120s)")
            AchievementService.update_progress(user, "speed-demon", 1)

    if instance.stars == 3:
        logger.info(f"3-star condition met for {user.username}")
        AchievementService.update_progress(user, "perfectionist", 1)


# ──── Streak-based achievements ────


@receiver(post_save, sender=DailyCheckIn)
def check_streak_achievements(sender, instance, created, **kwargs):
    """
    Check and unlock streak-based achievements.
    Only triggers when a new check-in is created, not on updates.
    """
    # Only process new check-ins
    if not created:
        logger.debug(f"Skipping streak check for existing check-in {instance.id}")
        return

    user = instance.user

    # Calculate the ACTUAL consecutive streak (not cycle day)
    # Count consecutive days from today backwards
    from datetime import timedelta

    from django.utils import timezone

    today = timezone.now().date()
    consecutive_streak = 0
    check_date = today

    # Count backwards from today to find consecutive check-ins
    while True:
        check_exists = DailyCheckIn.objects.filter(user=user, check_in_date=check_date).exists()

        if check_exists:
            consecutive_streak += 1
            check_date -= timedelta(days=1)
        else:
            break  # Streak broken

    logger.info(f"User {user.username} check-in on {today}: consecutive_streak={consecutive_streak}, cycle_day={instance.streak_day}")

    # Update progress for streak achievements
    # Only if consecutive_streak >= 1 (meaning they actually have a streak)
    if consecutive_streak >= 1:
        AchievementService.update_progress(user, "streak-starter", consecutive_streak)
        AchievementService.update_progress(user, "streak-master", consecutive_streak)


# ──── Social achievements ────


@receiver(post_save, sender=UserFollow)
def check_social_achievements(sender, instance, created, **kwargs):
    """
    Check and unlock social achievements when a user follows someone.
    Only triggers on new follow relationships.
    """
    # Only process new follows
    if not created:
        logger.debug(f"Skipping social check for existing follow {instance.id}")
        return

    follower = instance.follower
    following_count = UserFollow.objects.filter(follower=follower).count()

    logger.info(f"Social achievements check for {follower.username}: following_count={following_count}")

    AchievementService.update_progress(follower, "socializer", following_count)
    AchievementService.update_progress(follower, "networker", following_count)
