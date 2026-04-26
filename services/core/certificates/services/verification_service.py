from ..models import CertificateVerificationLog, UserCertificate
from .base_certificate_service import BaseCertificateService


class VerificationService(BaseCertificateService):
    """Handles logic for certificate verification and logging."""

    @staticmethod
    def verify_certificate(certificate_id, request=None):
        """
        Verifies a certificate and logs the attempt.
        """
        try:
            certificate = UserCertificate.objects.get(certificate_id=certificate_id)

            # Log the verification attempt
            ip_address = None
            user_agent = None
            referer = None

            if request:
                x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(",")[0]
                else:
                    ip_address = request.META.get("REMOTE_ADDR")

                user_agent = request.META.get("HTTP_USER_AGENT")
                referer = request.META.get("HTTP_REFERER")

            CertificateVerificationLog.objects.create(
                certificate=certificate,
                ip_address=ip_address,
                user_agent=user_agent,
                referer=referer,
            )

            VerificationService.log_event(
                "CERT_VERIFIED",
                certificate_id=certificate_id,
                details={"valid": certificate.is_valid, "ip": ip_address},
            )

            return certificate, True
        except UserCertificate.DoesNotExist:
            VerificationService.log_event("CERT_VERIFY_FAILED", certificate_id=certificate_id)
            return None, False
