import hmac
import logging
import time
from hashlib import sha256
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


def build_internal_headers(path: str) -> dict[str, str]:
    headers = {"X-Internal-API-Key": settings.INTERNAL_API_KEY}
    signing_secret = (settings.INTERNAL_SIGNING_SECRET or "").strip()
    if signing_secret:
        timestamp = str(int(time.time()))
        signature = hmac.new(
            signing_secret.encode("utf-8"),
            f"{timestamp}:{path}".encode("utf-8"),
            sha256,
        ).hexdigest()
        headers["X-Internal-Timestamp"] = timestamp
        headers["X-Internal-Signature"] = signature
    return headers


def authorize_internal_request(
    path: str,
    api_key: Optional[str],
    timestamp: Optional[str],
    signature: Optional[str],
) -> bool:
    if api_key != settings.INTERNAL_API_KEY:
        return False

    signing_secret = (settings.INTERNAL_SIGNING_SECRET or "").strip()
    if not signing_secret:
        return not settings.INTERNAL_REQUIRE_SIGNATURE

    if not timestamp or not signature:
        return False
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False

    if abs(int(time.time()) - ts) > 120:
        return False

    expected = hmac.new(
        signing_secret.encode("utf-8"),
        f"{timestamp}:{path}".encode("utf-8"),
        sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
