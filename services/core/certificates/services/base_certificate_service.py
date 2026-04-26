import logging

logger = logging.getLogger(__name__)


class BaseCertificateService:
    """Base logic for certificate operations."""

    @staticmethod
    def get_required_challenges():
        """Returns total number of challenges required for a certificate."""
        from challenges.models import Challenge

        return Challenge.objects.filter(created_for_user__isnull=True).count()

    @staticmethod
    def log_event(action, user=None, certificate_id=None, details=None):
        """Logs certificate-related events for auditing."""
        user_info = f"user={user.username}" if user else "user=Anonymous"
        cert_info = f"cert={certificate_id}" if certificate_id else ""
        msg = f"CERT_EVENT: action={action} {user_info} {cert_info} details={details or {}}"
        logger.info(msg)
