import logging

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import transaction
from users.models import UserProfile

from ..tasks import send_welcome_email_task
from ..utils import (
    generate_tokens,
    get_github_access_token,
    get_github_user,
    get_github_user_email,
    get_google_access_token,
    get_google_user,
)
from .base_auth_service import BaseAuthService

logger = logging.getLogger(__name__)


class OAuthService(BaseAuthService):
    @staticmethod
    def get_github_auth_url(state=None):
        from urllib.parse import urlencode

        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
            "scope": "user:email",
        }
        if state:
            params["state"] = state
        return f"https://github.com/login/oauth/authorize?{urlencode(params)}"

    @staticmethod
    def get_google_auth_url(state=None):
        from urllib.parse import urlencode

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
            "access_type": "offline",
            "prompt": "select_account",
        }
        if state:
            params["state"] = state
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    @staticmethod
    def handle_oauth_login(provider, code, request=None):
        token_data = OAuthService._exchange_code_for_token(provider, code)
        if "error" in token_data:
            OAuthService.log_security_event(
                action="OAUTH_LOGIN_FAILURE",
                details={
                    "provider": provider,
                    "error": "Token exchange failed",
                    "raw": token_data,
                },
                request=request,
            )
            return None, token_data

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token", "")

        user_info = OAuthService._get_provider_user_info(provider, access_token)
        if "error" in user_info:
            OAuthService.log_security_event(
                action="OAUTH_LOGIN_FAILURE",
                details={
                    "provider": provider,
                    "error": "User info fetch failed",
                    "raw": user_info,
                },
                request=request,
            )
            return None, user_info

        with transaction.atomic():
            user = OAuthService._match_or_create_user(
                provider=provider,
                user_info=user_info,
                tokens={"access": access_token, "refresh": refresh_token},
            )

        if not user.is_active:
            OAuthService.log_security_event(
                action="LOGIN_BLOCKED",
                user=user,
                details={"provider": provider, "reason": "Account disabled"},
                request=request,
            )
            return None, {"error": "User account is disabled."}

        jwt_tokens = generate_tokens(user)

        OAuthService.log_security_event(
            action="OAUTH_LOGIN_SUCCESS",
            user=user,
            details={"provider": provider},
            request=request,
        )

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
        provider_id = user_info["id"]
        email = user_info["email"]

        try:
            profile = UserProfile.objects.select_related("user").get(provider=provider, provider_id=provider_id)
            profile.access_token = tokens["access"]
            profile.refresh_token = tokens["refresh"]
            profile.save()
            return profile.user
        except UserProfile.DoesNotExist:
            pass

        user = None
        if email:
            user = User.objects.filter(email=email).first()

        if user:
            OAuthService._create_profile(user, provider, user_info, tokens)
            return user

        username = OAuthService._generate_unique_username(user_info["username"])
        name_parts = user_info["name"].split(" ", 1) if user_info["name"] else ["", ""]
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = User.objects.create_user(
            username=username,
            email=email or "",
            first_name=first_name,
            last_name=last_name,
        )

        OAuthService._create_profile(user, provider, user_info, tokens)
        send_welcome_email_task.delay(user.id)
        return user

    @staticmethod
    def _create_profile(user, provider, user_info, tokens):
        profile = getattr(user, "profile", None)
        if profile:
            profile.provider = provider
            profile.provider_id = user_info["id"]
            profile.access_token = tokens["access"]
            profile.refresh_token = tokens["refresh"]
            profile.save()
            if not profile.avatar and user_info.get("avatar_url"):
                OAuthService._download_and_save_avatar(profile, user_info["avatar_url"])
        else:
            profile = UserProfile.objects.create(
                user=user,
                provider=provider,
                provider_id=user_info["id"],
                access_token=tokens["access"],
                refresh_token=tokens["refresh"],
            )
            if user_info.get("avatar_url"):
                OAuthService._download_and_save_avatar(profile, user_info["avatar_url"])

    @staticmethod
    def _download_and_save_avatar(profile, url):
        try:
            headers = {"User-Agent": "CLASHCODE-Backend/1.0"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                file_name = url.split("/")[-1].split("?")[0]
                if not file_name or len(file_name) < 4:
                    file_name = f"avatar_{profile.user.id}.png"
                if "." not in file_name:
                    file_name += ".png"
                profile.avatar.save(file_name, ContentFile(response.content), save=True)
                logger.info(f"Successfully downloaded avatar for user {profile.user.username}")
        except Exception as e:
            logger.error(f"Failed to download avatar from {url}: {e}")

    @staticmethod
    def _generate_unique_username(base_username):
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
        return username
