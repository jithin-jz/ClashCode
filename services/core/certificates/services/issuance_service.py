from django.db import transaction

from ..models import UserCertificate
from .base_certificate_service import BaseCertificateService
from .eligibility_service import EligibilityService


class IssuanceService(BaseCertificateService):
    """Handles logic for issuing and updating certificates."""

    @staticmethod
    def get_or_create_certificate(user):
        """
        Retrieves an existing certificate or creates a new one if user is eligible.
        Also updates completion_count if necessary.
        """
        if not EligibilityService.is_eligible(user):
            completed = EligibilityService.get_completed_count(user)
            required = EligibilityService.get_required_challenges()
            raise ValueError(f"User not eligible. Completed {completed}/{required} challenges.")

        with transaction.atomic():
            certificate, created = UserCertificate.objects.get_or_create(
                user=user,
                defaults={"completion_count": EligibilityService.get_completed_count(user)},
            )

            current_count = EligibilityService.get_completed_count(user)
            if not created and current_count != certificate.completion_count:
                certificate.completion_count = current_count
                certificate.save(update_fields=["completion_count"])
                IssuanceService.log_event("CERT_UPDATED", user=user, certificate_id=certificate.certificate_id)
            elif created:
                IssuanceService.log_event("CERT_ISSUED", user=user, certificate_id=certificate.certificate_id)
                # Here is where we would trigger background image generation
                # IssuanceService.trigger_image_generation(certificate)

            return certificate

    @staticmethod
    def trigger_image_generation(certificate):
        """Place holder for background task triggering."""
        # from .tasks import generate_certificate_image
        # generate_certificate_image.delay(certificate.id)
        pass
