import logging

from django.contrib.auth.models import User

from ..utils import (
    decode_token,
    generate_tokens,
)
from .base_auth_service import BaseAuthService

logger = logging.getLogger(__name__)


class TokenService(BaseAuthService):
    @staticmethod
    def rotate_refresh_token(user, old_payload: dict, request=None):
        """
        Invalidates the old refresh token and issues a new pair.
        """
        TokenService.blacklist_token(old_payload)
        tokens = generate_tokens(user)
        TokenService.log_security_event(
            action="REFRESH_TOKEN_ROTATION",
            user=user,
            request=request,
            details={"jti_revoked": old_payload.get("jti")},
        )
        return tokens

    @staticmethod
    def refresh_access_token(token):
        """
        Validates a refresh token and returns the user if valid.
        """
        if not token:
            return None, "Refresh token is required"

        payload = decode_token(token)
        if not payload or payload.get("type") != "refresh":
            return None, "Invalid or expired refresh token"

        if TokenService.is_token_blacklisted(payload.get("jti")):
            return None, "Invalid or expired refresh token"

        try:
            user = User.objects.get(id=payload["user_id"])
            if not user.is_active:
                return None, "User account is disabled."
            return user, payload
        except User.DoesNotExist:
            return None, "Invalid or expired refresh token"
