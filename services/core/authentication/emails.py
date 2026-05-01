import logging
from datetime import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _display_name(user):
    return (user.first_name or user.username or "Coder").strip()


def _avatar_url(user):
    profile = getattr(user, "profile", None)
    avatar = getattr(profile, "avatar", None) if profile else None
    if not avatar:
        return ""
    try:
        url = avatar.url
    except Exception:
        return ""

    if url.startswith("http://") or url.startswith("https://"):
        return url

    base_url = settings.BACKEND_URL.rstrip("/")
    return f"{base_url}{url}"


def send_welcome_email(user):
    """
    Send a welcome email to a newly registered user using a Django template.
    """
    subject = "Welcome to CLASHCODE"

    context = {
        "name": _display_name(user),
        "avatar_url": _avatar_url(user),
        "frontend_url": settings.FRONTEND_URL,
        "year": datetime.now().year,
    }

    try:
        html_message = render_to_string("emails/welcome_email.html", context)

        # Simple plain text fallback
        plain_message = (
            f"Welcome to CLASHCODE.\n\n"
            f"Hi {context['name']},\n\n"
            "Your account is ready.\n"
            f"Start with your first challenge: {settings.FRONTEND_URL}\n\n"
            "— CLASHCODE"
        )

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=None,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info("Welcome email sent to %s", user.email)

    except Exception:
        logger.exception("Failed to send welcome email to %s", user.email)


def send_otp_email(email, otp):
    """
    Send an OTP email for login verification using a Django template.
    """
    subject = "Your Login Code - CLASHCODE"

    context = {
        "otp": otp,
        "year": datetime.now().year,
    }

    try:
        html_message = render_to_string("emails/otp_email.html", context)

        plain_message = (
            f"Your CLASHCODE login code is {otp}.\n\n"
            "This code expires in 10 minutes.\n"
            "If you didn’t request this, ignore this email."
        )

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=None,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info("OTP email sent to %s", email)
        return True

    except Exception:
        logger.exception("Failed to send OTP email to %s", email)
        return False
