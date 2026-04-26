import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction

from ..utils import decode_token
from .base_auth_service import BaseAuthService

logger = logging.getLogger(__name__)


class AccountService(BaseAuthService):
    @staticmethod
    def handle_logout(request):
        """
        Handles user logout by blacklisting current tokens.
        """
        user = getattr(request, "user", None)
        if user and not user.is_authenticated:
            user = None

        # Blacklist from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and " " in auth_header:
            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            if payload:
                AccountService.blacklist_token(payload)

        # Blacklist from cookie
        token_cookie = request.COOKIES.get(settings.JWT_ACCESS_COOKIE_NAME)
        if token_cookie:
            payload = decode_token(token_cookie)
            if payload:
                AccountService.blacklist_token(payload)

        AccountService.log_security_event(action="LOGOUT", user=user, request=request)

    @staticmethod
    def delete_user_account(user_id, request=None):
        """
        Permanently deletes a user account.
        """
        try:
            with transaction.atomic():
                user = User.objects.select_for_update().get(id=user_id)
                username = user.username
                email = user.email
                user.delete()

                AccountService.log_security_event(
                    action="ACCOUNT_DELETED",
                    email=email,
                    request=request,
                    details={"original_username": username},
                )
                return True, None
        except Exception:
            logger.exception(f"DeleteAccount failed for user_id={user_id}")
            return (
                False,
                "Failed to delete account. Please try again or contact support.",
            )
