"""Internal service authentication for the executor."""

import hmac
import logging
import os
import time
from hashlib import sha256

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "").strip()
INTERNAL_SIGNING_SECRET = os.getenv("INTERNAL_SIGNING_SECRET", "").strip()
REQUIRE_SIGNATURE = os.getenv("INTERNAL_REQUIRE_SIGNATURE", "true").lower() == "true"
MAX_TIMESTAMP_SKEW = 120  # seconds


def _timing_safe_equal(left: str, right: str) -> bool:
    return hmac.compare_digest((left or "").strip(), (right or "").strip())


async def verify_internal_auth(request: Request) -> None:
    """
    Verify that the request comes from an authorized internal service.

    Checks:
    1. X-Internal-API-Key matches INTERNAL_API_KEY
    2. (If signing enabled) HMAC signature over timestamp:path is valid and fresh
    """
    # Skip auth in development if no key is configured
    if not INTERNAL_API_KEY:
        logger.warning("INTERNAL_API_KEY not set — executor auth disabled (dev mode)")
        return

    # 1. Verify API key
    request_key = request.headers.get("X-Internal-API-Key", "").strip()
    if not _timing_safe_equal(request_key, INTERNAL_API_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API key")

    # 2. Verify HMAC signature if required
    if not REQUIRE_SIGNATURE or not INTERNAL_SIGNING_SECRET:
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
        INTERNAL_SIGNING_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        sha256,
    ).hexdigest()

    if not _timing_safe_equal(signature, expected):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid signature")
