import logging

from celery import shared_task

from .emails import send_otp_email, send_welcome_email

logger = logging.getLogger(__name__)


@shared_task
def send_welcome_email_task(user_id):
    """
    Async task to send welcome email.
    We pass user_id because passing complex objects (User) to Celery is an anti-pattern.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
        send_welcome_email(user)
        logger.info(f"Welcome email task completed for user {user_id}")
        return {"status": "sent", "user_id": user_id}
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found for welcome email task")
        return {"status": "user_not_found", "user_id": user_id}
    except Exception as e:
        logger.exception(f"Welcome email task failed: {str(e)}")
        return {"status": "error", "error": str(e)}


@shared_task
def send_otp_email_task(email, otp):
    """
    Async task to send OTP email.
    """
    try:
        send_otp_email(email, otp)
        logger.info(f"OTP email task completed for {email}")
        return {"status": "sent", "email": email}
    except Exception as e:
        logger.exception(f"OTP email task failed: {str(e)}")
        return {"status": "error", "error": str(e)}


@shared_task
def fetch_oauth_avatar_task(profile_id, url):
    try:
        from users.models import UserProfile

        from .services import AuthService

        profile = UserProfile.objects.get(pk=profile_id)
        AuthService._download_and_save_avatar(profile, url)
        logger.info("OAuth avatar task completed for profile %s", profile_id)
        return {"status": "saved", "profile_id": profile_id}
    except UserProfile.DoesNotExist:
        logger.warning("Profile %s not found for avatar task", profile_id)
        return {"status": "profile_not_found", "profile_id": profile_id}
    except Exception as e:
        logger.exception("OAuth avatar task failed: %s", str(e))
        return {"status": "error", "error": str(e)}
