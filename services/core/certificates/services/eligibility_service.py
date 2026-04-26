from challenges.models import Challenge, UserProgress

from .base_certificate_service import BaseCertificateService


class EligibilityService(BaseCertificateService):
    """Handles logic for determining if a user is eligible for a certificate."""

    @staticmethod
    def get_completed_count(user):
        """Calculates how many unique required challenges the user has completed."""
        required_orders = set(Challenge.objects.filter(created_for_user__isnull=True).values_list("order", flat=True))
        completed_orders = set(
            UserProgress.objects.filter(
                user=user,
                status=UserProgress.Status.COMPLETED,
                challenge__created_for_user__isnull=True,
            ).values_list("challenge__order", flat=True)
        )
        return len(required_orders.intersection(completed_orders))

    @staticmethod
    def is_eligible(user):
        """Checks if user meets the minimum requirements for certificate issuance."""
        completed_count = EligibilityService.get_completed_count(user)
        return completed_count >= EligibilityService.get_required_challenges()

    @staticmethod
    def get_eligibility_status(user):
        """Returns a detailed breakdown of user's eligibility."""
        completed_count = EligibilityService.get_completed_count(user)
        required = EligibilityService.get_required_challenges()
        is_eligible = completed_count >= required

        # We'll use issuance check later to avoid circularity if possible
        from ..models import UserCertificate

        has_cert = UserCertificate.objects.filter(user=user, is_valid=True).exists()

        return {
            "eligible": is_eligible,
            "completed_challenges": completed_count,
            "required_challenges": required,
            "has_certificate": has_cert,
            "remaining_challenges": max(0, required - completed_count),
        }
