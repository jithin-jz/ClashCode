import logging
from datetime import datetime, timezone

from django.core.cache import cache

from ..models import SecurityAuditLog

logger = logging.getLogger(__name__)


class BaseAuthService:
    @staticmethod
    def log_security_event(action, user=None, email=None, request=None, details=None):
        """
        Logs a security-sensitive event.
        """
        ip = None
        ua = ""
        if request:
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip = x_forwarded_for.split(",")[0].strip()
            else:
                ip = request.META.get("REMOTE_ADDR")
            ua = request.META.get("HTTP_USER_AGENT", "")[:512]

        SecurityAuditLog.objects.create(
            user=user,
            email=email or (user.email if user else ""),
            action=action,
            ip_address=ip,
            user_agent=ua,
            details=details or {},
        )
        logger.info(f"Security Event: {action} | User: {user.username if user else email} | IP: {ip}")

    @staticmethod
    def _cache_get(key: str, default=None):
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
    def blacklist_token(payload: dict):
        """Adds a token's JTI to the blacklist until it expires."""
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or not exp:
            return

        now = datetime.now(timezone.utc).timestamp()
        timeout = int(exp - now)

        if timeout > 0:
            BaseAuthService._cache_set(f"auth:blacklist:{jti}", "1", timeout=timeout)

    @staticmethod
    def is_token_blacklisted(jti: str) -> bool:
        """Checks if a token JTI is in the blacklist."""
        if not jti:
            return False
        return BaseAuthService._cache_get(f"auth:blacklist:{jti}") is not None
