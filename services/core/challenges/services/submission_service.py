from django.db import transaction
from django.utils import timezone
from xpoint.services import XPService

from ..models import UserProgress
from .base_challenge_service import BaseChallengeService


class SubmissionService(BaseChallengeService):
    """Handles logic for processing code submissions and calculating rewards."""

    @staticmethod
    def process_submission_result(user, challenge, passed=False):
        """Processes the outcome of a code submission."""
        if not passed:
            return {"status": "failed"}

        xp_earned = 0
        with transaction.atomic():
            # Lock the progress row so concurrent submissions cannot both see
            # "not completed yet" and award XP twice.
            progress, _ = UserProgress.objects.select_for_update().get_or_create(user=user, challenge=challenge)
            stars = SubmissionService.calculate_stars(progress, challenge)
            newly_completed = progress.status != UserProgress.Status.COMPLETED

            if newly_completed or stars > progress.stars:
                progress.status = UserProgress.Status.COMPLETED
                progress.completed_at = timezone.now()
                progress.stars = max(progress.stars, stars)
                progress.save()

                if newly_completed:
                    xp_earned = challenge.xp_reward
                    XPService.add_xp(user, xp_earned, source="challenge_completion")

        if newly_completed:
            SubmissionService.log_activity(
                "COMPLETED",
                user,
                challenge,
                details={"stars": stars, "xp": xp_earned},
            )

        from .progression_service import ProgressionService

        next_challenge = ProgressionService.get_next_challenge(challenge)

        return {
            "status": "completed" if newly_completed else "already_completed",
            "xp_earned": xp_earned,
            "stars": stars,
            "next_level_slug": next_challenge.slug if next_challenge else None,
        }

    @staticmethod
    def calculate_stars(progress, challenge):
        """Calculates star rating (1-3) based on hints and time."""
        stars = 3

        # Penalty for AI hints
        stars -= progress.ai_hints_purchased

        # Penalty for slow completion
        if progress.started_at:
            duration = (timezone.now() - progress.started_at).total_seconds()
            if duration > 2 * challenge.target_time_seconds:
                stars -= 1

        return max(1, stars)
