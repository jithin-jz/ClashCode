import logging

from ..models import UserProgress

logger = logging.getLogger(__name__)


class BaseChallengeService:
    """Base utilities for challenge services."""

    @staticmethod
    def get_progress(user, challenge):
        """Helper to get or create progress for a user and challenge."""
        return UserProgress.objects.get_or_create(user=user, challenge=challenge)

    @staticmethod
    def log_activity(action, user, challenge, details=None):
        """Standardized logging for challenge activities."""
        msg = f"CHALLENGE_ACTIVITY: action={action} user={user.username} challenge={challenge.slug}"
        if details:
            msg += f" details={details}"
        logger.info(msg)
