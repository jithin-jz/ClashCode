from .eligibility_service import EligibilityService
from .issuance_service import IssuanceService
from .verification_service import VerificationService


class CertificateService(EligibilityService, IssuanceService, VerificationService):
    """
    Unified Certificate Service.
    Combines eligibility, issuance, and verification logic.
    """

    @staticmethod
    def has_certificate(user):
        """Checks if user has a valid certificate."""
        certificate = getattr(user, "certificate", None)
        if not certificate:
            return False
        required = CertificateService.get_required_challenges()
        return bool(certificate.is_valid and certificate.completion_count >= required)
