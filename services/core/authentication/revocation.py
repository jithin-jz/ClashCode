"""
Cross-service token revocation.

Core keeps its own blacklist in the Django cache. The chat service verifies JWTs
on its own and cannot read that cache, so revocations are also mirrored to plain
Redis keys (no Django key prefix) that chat checks on every WebSocket connect:

    auth:revoked_jti:<jti>        set on logout / refresh rotation, expires with the token
    auth:disabled_user:<user_id>  present while the account is disabled

Failures are logged and swallowed: core's own checks stay authoritative.
"""

import logging
import os

import redis
from django.conf import settings

logger = logging.getLogger(__name__)

REVOKED_JTI_KEY = "auth:revoked_jti:{jti}"
DISABLED_USER_KEY = "auth:disabled_user:{user_id}"

_client = None


def _enabled() -> bool:
    return getattr(settings, "AUTH_REVOCATION_REDIS_ENABLED", True)


def _redis():
    global _client
    if _client is None:
        _client = redis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379/0"),
            socket_timeout=2,
            socket_connect_timeout=2,
        )
    return _client


def revoke_jti(jti: str, ttl_seconds: int) -> None:
    if not _enabled() or not jti or ttl_seconds <= 0:
        return
    try:
        _redis().set(REVOKED_JTI_KEY.format(jti=jti), "1", ex=ttl_seconds)
    except Exception:
        logger.exception("Failed to mirror token revocation to Redis")


def set_user_disabled(user_id: int, disabled: bool) -> None:
    if not _enabled():
        return
    key = DISABLED_USER_KEY.format(user_id=user_id)
    try:
        if disabled:
            _redis().set(key, "1")
        else:
            _redis().delete(key)
    except Exception:
        logger.exception("Failed to mirror account status to Redis")
