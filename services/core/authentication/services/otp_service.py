import hmac
import logging
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from users.models import UserProfile

from ..emails import send_otp_email
from ..models import EmailOTP
from ..tasks import (
    send_otp_email_task,
    send_welcome_email_task,
)
from ..utils import (
    generate_otp_code,
    generate_tokens,
    hash_otp,
)
from .base_auth_service import BaseAuthService

logger = logging.getLogger(__name__)


class OTPService(BaseAuthService):
    OTP_VERIFY_MAX_ATTEMPTS = 5
    OTP_VERIFY_WINDOW_SECONDS = 10 * 60
    OTP_VERIFY_LOCK_SECONDS = 15 * 60
    OTP_REQUEST_WINDOW_SECONDS = 10 * 60
    OTP_REQUEST_MAX = 5

    @staticmethod
    def _otp_attempts_key(email: str) -> str:
        return f"auth:otp:verify_attempts:{email.lower().strip()}"

    @staticmethod
    def _otp_lock_key(email: str) -> str:
        return f"auth:otp:verify_lock:{email.lower().strip()}"

    @staticmethod
    def _otp_request_key(email: str) -> str:
        return f"auth:otp:request_count:{email.lower().strip()}"

    @staticmethod
    def request_otp(email):
        email = email.lower().strip()
        request_key = OTPService._otp_request_key(email)
        request_count = OTPService._cache_get(request_key, 0) or 0
        if request_count >= OTPService.OTP_REQUEST_MAX:
            raise ValidationError("Too many OTP requests. Please try again later.")

        otp_code = generate_otp_code()
        otp_hash = hash_otp(email, otp_code)
        EmailOTP.objects.create(email=email, otp=otp_hash)

        delivery_ok = True
        if settings.OTP_EMAIL_ASYNC:
            try:
                send_otp_email_task.delay(email, otp_code)
            except Exception:
                logger.exception("Failed to enqueue OTP email task fallback to sync for %s", email)
                delivery_ok = send_otp_email(email, otp_code)
        else:
            delivery_ok = send_otp_email(email, otp_code)

        OTPService._cache_set(
            request_key,
            request_count + 1,
            timeout=OTPService.OTP_REQUEST_WINDOW_SECONDS,
        )

        if not delivery_ok:
            raise ValidationError("Failed to deliver OTP email. Please try again later.")
        return {"ok": True}

    @staticmethod
    def verify_otp(email, otp, request=None):
        email = email.lower().strip()
        otp = otp.strip()
        lock_key = OTPService._otp_lock_key(email)
        attempts_key = OTPService._otp_attempts_key(email)

        if OTPService._cache_get(lock_key):
            OTPService.log_security_event(action="OTP_VERIFY_LOCKED", email=email, request=request)
            return None, {"error": "Too many invalid attempts. Try again later."}

        expiry_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        otp_hash = hash_otp(email, otp)
        otp_candidates = list(
            EmailOTP.objects.filter(email__iexact=email, created_at__gte=expiry_time).order_by("-created_at")[:5]
        )
        otp_record = next(
            (item for item in otp_candidates if hmac.compare_digest(item.otp, otp_hash)),
            None,
        )

        if otp_record is None:
            attempts = (OTPService._cache_get(attempts_key, 0) or 0) + 1
            OTPService._cache_set(attempts_key, attempts, timeout=OTPService.OTP_VERIFY_WINDOW_SECONDS)
            OTPService.log_security_event(
                action="OTP_VERIFY_FAILURE",
                email=email,
                details={"attempt": attempts},
                request=request,
            )
            if attempts >= OTPService.OTP_VERIFY_MAX_ATTEMPTS:
                OTPService._cache_set(lock_key, 1, timeout=OTPService.OTP_VERIFY_LOCK_SECONDS)
            return None, {"error": "Invalid or expired OTP."}

        try:
            with transaction.atomic():
                user = User.objects.filter(email__iexact=email).first()
                is_new_user = user is None
                if not user:
                    username = email.split("@")[0]
                    username = OTPService._generate_unique_username(username)
                    user = User.objects.create_user(username=username, email=email)
                    UserProfile.objects.get_or_create(user=user, defaults={"provider": "email", "provider_id": email})
                    send_welcome_email_task.delay(user.id)
                else:
                    UserProfile.objects.get_or_create(user=user, defaults={"provider": "email", "provider_id": email})

                otp_record.delete()
                OTPService._cache_delete(attempts_key)
                OTPService._cache_delete(lock_key)
                tokens = generate_tokens(user)

            if not user.is_active:
                OTPService.log_security_event(
                    action="LOGIN_BLOCKED",
                    user=user,
                    details={"reason": "Account disabled"},
                    request=request,
                )
                return None, {"error": "User account is disabled."}

            OTPService.log_security_event(
                action=("OTP_LOGIN_SUCCESS" if not is_new_user else "OTP_REGISTER_SUCCESS"),
                user=user,
                request=request,
            )
            return user, tokens
        except Exception as e:
            logger.exception(f"Error in verify_otp: {e}")
            return None, {"error": "Internal server error during login."}

    @staticmethod
    def _generate_unique_username(base_username):
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
        return username
