from django.utils import timezone

from ..models import Challenge, UserProgress
from .base_challenge_service import BaseChallengeService


class ProgressionService(BaseChallengeService):
    """Handles challenge locking, unlocking, and status annotation."""

    @staticmethod
    def get_annotated_challenges(user, queryset=None):
        """
        Returns a list of challenges annotated with status and stars for the given user.
        Handles the implicit locking logic.
        """
        if queryset is None:
            queryset = Challenge.objects.all()

        challenges = queryset.order_by("order")
        progress_map = {p.challenge_id: p for p in UserProgress.objects.filter(user=user)}

        results = []
        previous_completed = True  # First challenge is unlocked by default

        for challenge in challenges:
            p = progress_map.get(challenge.id)
            status = UserProgress.Status.LOCKED
            stars = 0

            if p:
                status = p.status
                stars = p.stars

            if status == UserProgress.Status.LOCKED and previous_completed:
                status = UserProgress.Status.UNLOCKED

            challenge.user_status = status
            challenge.user_stars = stars
            results.append(challenge)

            previous_completed = status == UserProgress.Status.COMPLETED

        return results

    @staticmethod
    def get_challenge_details(user, challenge):
        """Retrieves detailed challenge info and ensures start time is tracked."""
        progress, _ = ProgressionService.get_progress(user, challenge)

        if not progress.started_at:
            progress.started_at = timezone.now()
            progress.save(update_fields=["started_at"])

        return {
            "status": progress.status,
            "stars": progress.stars,
            "ai_hints_purchased": progress.ai_hints_purchased,
            "started_at": progress.started_at,
        }

    @staticmethod
    def get_next_challenge(current_challenge):
        """Retrieves the next challenge in sequence."""
        return Challenge.objects.filter(order__gt=current_challenge.order).order_by("order").first()
