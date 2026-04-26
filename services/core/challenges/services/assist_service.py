from xpoint.services import XPService

from .base_challenge_service import BaseChallengeService


class AssistService(BaseChallengeService):
    """Handles AI assistance and hint purchases."""

    @staticmethod
    def purchase_ai_hint(user, challenge):
        """Purchases the next level of AI assistance."""
        progress, _ = AssistService.get_progress(user, challenge)

        if progress.ai_hints_purchased >= 3:
            raise PermissionError("Maximum of 3 AI hints allowed for this challenge.")

        cost = 10 * (progress.ai_hints_purchased + 1)

        try:
            # XPService.add_xp with negative value handles deduction
            remaining_xp = XPService.add_xp(user, -cost, source="ai_assist")
        except ValueError as exc:
            raise PermissionError("Insufficient XP") from exc

        progress.ai_hints_purchased += 1
        progress.save(update_fields=["ai_hints_purchased"])

        AssistService.log_activity(
            "PURCHASE_HINT",
            user,
            challenge,
            details={"level": progress.ai_hints_purchased, "cost": cost},
        )

        return remaining_xp
