import logging

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import QuerySet

from .models import Achievement, UserAchievement, UserAchievementProgress

logger = logging.getLogger(__name__)


class AchievementService:
    @staticmethod
    def get_user_visible_achievements(user: User) -> QuerySet:
        """
        Retrieves all achievements visible to the user.
        Includes all non-secret achievements and any secret ones they have unlocked.
        """
        qs = Achievement.objects.all()
        unlocked_ids = UserAchievement.objects.filter(user=user).values_list("achievement_id", flat=True)

        # Secret achievements are only visible if unlocked
        return qs.exclude(is_secret=True) | qs.filter(id__in=unlocked_ids, is_secret=True)

    @staticmethod
    def get_user_unlocked_achievements(username: str) -> QuerySet:
        """Retrieves achievements unlocked by a specific user."""
        return UserAchievement.objects.filter(user__username=username).select_related("achievement")

    @staticmethod
    def update_progress(user: User, slug: str, current_value: int) -> bool:
        """
        Updates progress for a specific achievement.
        If current_value >= target_value, the achievement is unlocked.

        Validation:
        - current_value must be > 0 (no progress with zero/negative values)
        - current_value must meet or exceed target_value to unlock
        - Already unlocked achievements are skipped
        """
        try:
            achievement = Achievement.objects.get(slug=slug)

            # Validate current_value is meaningful
            if current_value <= 0:
                logger.debug(f"Ignoring invalid progress update for {slug}: current_value={current_value} (must be > 0)")
                return False

            # Check if already unlocked
            if UserAchievement.objects.filter(user=user, achievement=achievement).exists():
                logger.debug(f"Achievement {slug} already unlocked for user {user.username}")
                return False

            with transaction.atomic():
                # Update or create progress
                progress, created = UserAchievementProgress.objects.get_or_create(user=user, achievement=achievement)

                # Only update if value is higher (prevent regressions if event order is weird)
                if current_value > progress.current_value:
                    old_value = progress.current_value
                    progress.current_value = current_value
                    progress.save()

                    logger.info(
                        f"Progress updated for {slug}: user={user.username}, {old_value} → {current_value}/{achievement.target_value}"
                    )

                # Check for unlock - must meet or exceed target_value
                if progress.current_value >= achievement.target_value:
                    logger.info(
                        f"🏆 Achievement UNLOCKED: {slug} for user {user.username}! "
                        f"(value={progress.current_value}, target={achievement.target_value})"
                    )
                    return AchievementService.grant_achievement(user, achievement)
                else:
                    logger.debug(
                        f"Achievement {slug} not yet unlocked: "
                        f"{progress.current_value}/{achievement.target_value} "
                        f"({achievement.target_value - progress.current_value} more needed)"
                    )

            return False
        except Achievement.DoesNotExist:
            logger.warning(f"Attempted to update progress for non-existent achievement: {slug}")
            return False
        except Exception as e:
            logger.error(f"Error updating achievement progress for {slug}: {e}", exc_info=True)
            return False

    @staticmethod
    def grant_achievement(user: User, achievement: Achievement) -> bool:
        """Grants an achievement and its rewards."""
        user_ach, created = UserAchievement.objects.get_or_create(user=user, achievement=achievement)

        if created:
            logger.info(f"User {user.username} unlocked achievement: {achievement.title}")

            # Grant XP Reward
            if achievement.xp_reward:
                profile = getattr(user, "profile", None)
                if profile:
                    profile.xp += achievement.xp_reward
                    profile.save(update_fields=["xp"])

            # TODO: Trigger Real-time Notification via Redis/WebSocket

        return created
