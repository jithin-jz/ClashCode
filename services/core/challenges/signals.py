import logging

from certificates.services import CertificateService
from django.db.models.signals import post_save
from django.dispatch import receiver
from learning.tasks import update_leaderboard_cache

from .models import UserProgress

logger = logging.getLogger(__name__)


@receiver(post_save, sender=UserProgress)
def auto_generate_certificate(sender, instance, created, **kwargs):
    """
    Automatically generate certificate when user completes all challenges.

    Triggered after UserProgress is saved with COMPLETED status.
    """
    # Keep signature compatible with Django signal kwargs.
    _ = sender, created, kwargs

    # Only trigger on completion
    if instance.status != UserProgress.Status.COMPLETED:
        return

    user = instance.user

    # Check if user is now eligible for certificate
    if not CertificateService.is_eligible(user):
        return

    # Check if certificate already exists
    if CertificateService.has_certificate(user):
        # Update completion count in case user completed more challenges
        try:
            certificate = user.certificate
            current_count = CertificateService.get_completed_count(user)
            if current_count != certificate.completion_count:
                certificate.completion_count = current_count
                certificate.save(update_fields=["completion_count"])
                logger.info(f"Auto-updated certificate for {user.username}: {certificate.completion_count} challenges")
        except Exception as e:
            logger.error(f"Failed to update certificate for {user.username}: {e}")
        return

    # Generate new certificate
    try:
        certificate = CertificateService.get_or_create_certificate(user)
        logger.info(f"Auto-generated certificate for {user.username} (ID: {certificate.certificate_id})")
    except ValueError as e:
        # User not eligible (shouldn't happen due to check above, but defensive)
        logger.warning(f"Certificate generation failed for {user.username}: {e}")
    except Exception as e:
        logger.error(
            f"Unexpected error generating certificate for {user.username}: {e}",
            exc_info=True,
        )


@receiver(post_save, sender=UserProgress)
def trigger_leaderboard_update_on_progress(sender, instance, created, **kwargs):
    """
    Trigger real-time leaderboard update when a challenge is completed.
    """
    if instance.status == UserProgress.Status.COMPLETED:
        update_leaderboard_cache.delay()
