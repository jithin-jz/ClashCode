"""Internal service authentication for the executor.

The executor has its own credentials (``EXECUTOR_API_KEY`` /
``EXECUTOR_SIGNING_SECRET``) so a compromise of the sandbox pod never yields
the platform-wide ``INTERNAL_*`` secrets. For single-key local setups the
``INTERNAL_*`` values are used as a fallback.

Auth fails closed: without a configured key every request is rejected, unless
``EXECUTOR_ALLOW_UNAUTHENTICATED=true`` is set explicitly (tests/local only).
"""

import hmac
import logging
import os
import time
from hashlib import sha256

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

MAX_TIMESTAMP_SKEW = 120  # seconds


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _api_key() -> str:
    return _env("EXECUTOR_API_KEY") or _env("INTERNAL_API_KEY")


def _signing_secret() -> str:
    return _env("EXECUTOR_SIGNING_SECRET") or _env("INTERNAL_SIGNING_SECRET")


def _require_signature() -> bool:
    return _env("INTERNAL_REQUIRE_SIGNATURE").lower() != "false"


def _allow_unauthenticated() -> bool:
    return _env("EXECUTOR_ALLOW_UNAUTHENTICATED").lower() == "true"


def _timing_safe_equal(left: str, right: str) -> bool:
    return hmac.compare_digest((left or "").strip(), (right or "").strip())


def auth_configuration_error() -> str | None:
    """Return a description of a broken auth setup, or None when it is usable."""
    if _allow_unauthenticated():
        return None
    if not _api_key():
        return "EXECUTOR_API_KEY (or INTERNAL_API_KEY) is not set"
    if _require_signature() and not _signing_secret():
        return "INTERNAL_REQUIRE_SIGNATURE is on but no EXECUTOR_SIGNING_SECRET/INTERNAL_SIGNING_SECRET is set"
    return None


async def verify_internal_auth(request: Request) -> None:
    """
    Verify that the request comes from an authorized internal service.

    Checks:
    1. X-Internal-API-Key matches the executor key
    2. (If signing enabled) HMAC signature over timestamp:path is valid and fresh
    """
    if _allow_unauthenticated():
        return

    config_error = auth_configuration_error()
    if config_error:
        logger.error(f"Executor auth misconfigured: {config_error}")
        raise HTTPException(status_code=503, detail="Executor authentication is not configured")

    request_key = request.headers.get("X-Internal-API-Key", "").strip()
    if not _timing_safe_equal(request_key, _api_key()):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API key")

    signing_secret = _signing_secret()
    if not signing_secret:
        # Only reachable when INTERNAL_REQUIRE_SIGNATURE=false.
        return

    timestamp = request.headers.get("X-Internal-Timestamp", "").strip()
    signature = request.headers.get("X-Internal-Signature", "").strip()

    if not timestamp or not signature:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing signature headers")

    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid timestamp") from None

    now = int(time.time())
    if abs(now - ts) > MAX_TIMESTAMP_SKEW:
        raise HTTPException(status_code=401, detail="Unauthorized: Request expired")

    message = f"{timestamp}:{request.url.path}"
    expected = hmac.HMAC(
        signing_secret.encode("utf-8"),
        message.encode("utf-8"),
        sha256,
    ).hexdigest()

    if not _timing_safe_equal(signature, expected):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid signature")
