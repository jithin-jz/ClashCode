import logging
import hmac
from datetime import datetime, timedelta, timezone

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.cache import cache

from users.models import UserProfile
from .models import EmailOTP
from .utils import (
    generate_tokens,
    generate_otp_code,
    hash_otp,
    get_github_access_token,
    get_github_user,
    get_github_user_email,
    get_google_access_token,
    get_google_user,
)
from .tasks import (
    fetch_oauth_avatar_task,
    send_otp_email_task,
    send_welcome_email_task,
)
from .emails import send_otp_email

logger = logging.getLogger(__name__)


class AuthService:
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
    def _cache_get(key: str, default=None):
        """
        Safe cache read.

        If Redis/cache is unavailable, auth should still function rather than 500.
        """
        try:
            return cache.get(key, default)
        except Exception:
            logger.exception("Cache get failed for key=%s", key)
            return default

    @staticmethod
    def _cache_set(key: str, value, timeout: int | None = None):
        try:
            cache.set(key, value, timeout=timeout)
        except Exception:
            logger.exception("Cache set failed for key=%s", key)

    @staticmethod
    def _cache_delete(key: str):
        try:
            cache.delete(key)
        except Exception:
            logger.exception("Cache delete failed for key=%s", key)

    @staticmethod
    def handle_oauth_login(provider, code):
        """
        Orchestrates the complete OAuth login lifecycle.

        Args:
            provider (str): The OAuth provider name ('github', 'google').
            code (str): The authorization code received from the frontend callback.

        Returns:
            tuple: (User object, tokens_dict) on success, or (None, error_dict) on failure.
        """
        # 1. Exchange code -> access_token
        token_data = AuthService._exchange_code_for_token(provider, code)
        if "error" in token_data:
            return None, token_data

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token", "")

        # 2. Get User Info
        user_info = AuthService._get_provider_user_info(provider, access_token)
        if "error" in user_info:
            return None, user_info

        # 3. Match or Create User (Atomic Transaction)
        with transaction.atomic():
            user = AuthService._match_or_create_user(
                provider=provider,
                user_info=user_info,
                tokens={"access": access_token, "refresh": refresh_token},
            )

        if not user.is_active:
            return None, {"error": "User account is disabled."}

        # 4. Generate JWTs
        jwt_tokens = generate_tokens(user)

        return user, jwt_tokens

    @staticmethod
    def _exchange_code_for_token(provider, code):
        if provider == "github":
            return get_github_access_token(code)
        elif provider == "google":
            return get_google_access_token(code)
        return {"error": "Invalid provider"}

    @staticmethod
    def _get_provider_user_info(provider, access_token):
        if provider == "github":
            user = get_github_user(access_token)
            if "id" not in user:
                return {"error": "Failed to fetch GitHub user"}

            # Normalize data
            email = user.get("email") or get_github_user_email(access_token)
            return {
                "id": str(user["id"]),
                "email": email,
                "username": user.get("login"),
                "name": user.get("name", ""),
                "avatar_url": user.get("avatar_url", ""),
            }

        elif provider == "google":
            user = get_google_user(access_token)
            if "id" not in user:
                return {"error": "Failed to fetch Google user"}

            return {
                "id": str(user["id"]),
                "email": user.get("email", ""),
                "username": user.get("email", "").split("@")[0],
                "name": user.get("name", ""),
                "avatar_url": user.get("picture", ""),
            }

        return {"error": "Invalid provider"}

    @staticmethod
    def _match_or_create_user(provider, user_info, tokens):
        """Determines which User to log in."""
        provider_id = user_info["id"]
        email = user_info["email"]

        # Check provider match
        try:
            profile = UserProfile.objects.select_related("user").get(
                provider=provider, provider_id=provider_id
            )
            profile.access_token = tokens["access"]
            profile.refresh_token = tokens["refresh"]
            profile.save()
            return profile.user

        except UserProfile.DoesNotExist:
            pass

        # Link accounts if email matches
        user = None
        if email:
            user = User.objects.filter(email=email).first()

        if user:
            logger.info(
                f"Linking existing user {user.username} (Email: {email}) to new {provider} profile"
            )
            AuthService._create_profile(user, provider, user_info, tokens)
            return user

        # Create new user
        username = AuthService._generate_unique_username(user_info["username"])

        name_parts = user_info["name"].split(" ", 1) if user_info["name"] else ["", ""]
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = User.objects.create_user(
            username=username,
            email=email or "",
            first_name=first_name,
            last_name=last_name,
        )

        AuthService._create_profile(user, provider, user_info, tokens)
        send_welcome_email_task.delay(user.id)

        return user

    @staticmethod
    def _create_profile(user, provider, user_info, tokens):
        """Creates or updates the UserProfile model."""
        profile = getattr(user, "profile", None)

        if profile:
            # Update legacy profile with new provider's info
            profile.provider = provider
            profile.provider_id = user_info["id"]
            profile.access_token = tokens["access"]
            profile.refresh_token = tokens["refresh"]
            profile.save()

            # Update avatar if missing
            if not profile.avatar and user_info.get("avatar_url"):
                # Download synchronously as worker might not be running in dev
                AuthService._download_and_save_avatar(profile, user_info["avatar_url"])

        else:
            # Create fresh profile
            profile = UserProfile.objects.create(
                user=user,
                provider=provider,
                provider_id=user_info["id"],
                access_token=tokens["access"],
                refresh_token=tokens["refresh"],
            )

            if user_info.get("avatar_url"):
                AuthService._download_and_save_avatar(profile, user_info["avatar_url"])

    @staticmethod
    def _download_and_save_avatar(profile, url):
        """Helper to download image from URL and save to ImageField."""
        try:
            # GitHub and others require a User-Agent header
            headers = {"User-Agent": "CLASHCODE-Backend/1.0"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                # Extract filename from URL or generate one
                file_name = url.split("/")[-1].split("?")[0]
                if not file_name or len(file_name) < 4:
                    file_name = f"avatar_{profile.user.id}.png"

                # Ensure valid extension
                if "." not in file_name:
                    file_name += ".png"

                profile.avatar.save(file_name, ContentFile(response.content), save=True)
                logger.info(f"Successfully downloaded avatar for user {profile.user.username}")
        except Exception as e:
            logger.error(f"Failed to download avatar from {url}: {e}")

    @staticmethod
    def _generate_unique_username(base_username):
        """Ensure username uniqueness."""
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
        return username

    @staticmethod
    def request_otp(email):
        """Generates and sends an OTP to the given email."""
        email = email.lower().strip()
        request_key = AuthService._otp_request_key(email)
        request_count = AuthService._cache_get(request_key, 0) or 0
        if request_count >= AuthService.OTP_REQUEST_MAX:
            raise ValidationError("Too many OTP requests. Please try again later.")

        otp_code = generate_otp_code()
        otp_hash = hash_otp(email, otp_code)

        EmailOTP.objects.create(email=email, otp=otp_hash)

        delivery_ok = True
        if settings.OTP_EMAIL_ASYNC:
            try:
                send_otp_email_task.delay(email, otp_code)
            except Exception:
                logger.exception(
                    "Failed to enqueue OTP email task. Falling back to sync send for %s",
                    email,
                )
                delivery_ok = send_otp_email(email, otp_code)
        else:
            delivery_ok = send_otp_email(email, otp_code)

        AuthService._cache_set(
            request_key,
            request_count + 1,
            timeout=AuthService.OTP_REQUEST_WINDOW_SECONDS,
        )

        if not delivery_ok:
            raise ValidationError(
                "Failed to deliver OTP email. Please try again later."
            )

        return {"ok": True}

    @staticmethod
    def verify_otp(email, otp):
        """Verifies the OTP and logs the user in (or creates them)."""
        logger.info("Verifying OTP for %s", email)

        email = email.lower().strip()
        otp = otp.strip()
        lock_key = AuthService._otp_lock_key(email)
        attempts_key = AuthService._otp_attempts_key(email)

        if AuthService._cache_get(lock_key):
            logger.warning(f"OTP locked for {email}")
            return None, {"error": "Too many invalid attempts. Try again later."}

        expiry_time = datetime.now(timezone.utc) - timedelta(minutes=10)

        otp_hash = hash_otp(email, otp)
        otp_candidates = list(
            EmailOTP.objects.filter(
                email__iexact=email,
                created_at__gte=expiry_time,
            ).order_by("-created_at")[:5]
        )
        otp_record = next(
            (
                item
                for item in otp_candidates
                if hmac.compare_digest(item.otp, otp_hash)
            ),
            None,
        )

        if otp_record is None:
            logger.warning(f"OTP not found or expired for {email}")
            attempts = (AuthService._cache_get(attempts_key, 0) or 0) + 1
            AuthService._cache_set(
                attempts_key, attempts, timeout=AuthService.OTP_VERIFY_WINDOW_SECONDS
            )
            if attempts >= AuthService.OTP_VERIFY_MAX_ATTEMPTS:
                AuthService._cache_set(
                    lock_key, 1, timeout=AuthService.OTP_VERIFY_LOCK_SECONDS
                )
            return None, {"error": "Invalid or expired OTP."}

        try:
            with transaction.atomic():
                user = User.objects.filter(email__iexact=email).first()

                if not user:
                    # Registration
                    logger.info(f"Creating new user for {email}")

                    username = email.split("@")[0]
                    username = AuthService._generate_unique_username(username)

                    user = User.objects.create_user(username=username, email=email)

                    if hasattr(user, "profile"):
                        profile = user.profile
                        profile.provider = "email"
                        profile.provider_id = email
                        profile.save()
                    else:
                        UserProfile.objects.create(
                            user=user,
                            provider="email",
                            provider_id=email,
                            access_token="",
                            refresh_token="",
                        )
                    send_welcome_email_task.delay(user.id)

                else:
                    # Login
                    logger.info(f"Found existing user {user.username} for {email}")

                    if not hasattr(user, "profile"):
                        UserProfile.objects.create(
                            user=user,
                            provider="email",
                            provider_id=email,
                            access_token="",
                            refresh_token="",
                        )

                otp_record.delete()
                AuthService._cache_delete(attempts_key)
                AuthService._cache_delete(lock_key)
                tokens = generate_tokens(user)

            if not user.is_active:
                return None, {"error": "User account is disabled."}

            return user, tokens

        except Exception as e:
            logger.exception(f"Error during user creation/login in verify_otp: {e}")
            return None, {"error": "Internal server error during login."}
