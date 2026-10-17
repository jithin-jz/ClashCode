import hmac
import logging
import time
from hashlib import sha256

from config import settings

logger = logging.getLogger(__name__)


def _signed_headers(path: str, api_key: str, signing_secret: str) -> dict[str, str]:
    headers = {"X-Internal-API-Key": api_key}
    if signing_secret:
        timestamp = str(int(time.time()))
        signature = hmac.new(
            signing_secret.encode("utf-8"),
            f"{timestamp}:{path}".encode(),
            sha256,
        ).hexdigest()
        headers["X-Internal-Timestamp"] = timestamp
        headers["X-Internal-Signature"] = signature
    return headers


def build_internal_headers(path: str) -> dict[str, str]:
    return _signed_headers(path, settings.INTERNAL_API_KEY, (settings.INTERNAL_SIGNING_SECRET or "").strip())


def build_executor_headers(path: str) -> dict[str, str]:
    return _signed_headers(
        path,
        (settings.EXECUTOR_API_KEY or "").strip() or settings.INTERNAL_API_KEY,
        (settings.EXECUTOR_SIGNING_SECRET or "").strip() or (settings.INTERNAL_SIGNING_SECRET or "").strip(),
    )


def authorize_internal_request(
    path: str,
    api_key: str | None,
    timestamp: str | None,
    signature: str | None,
) -> bool:
    if not hmac.compare_digest((api_key or "").encode(), settings.INTERNAL_API_KEY.encode()):
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
        f"{timestamp}:{path}".encode(),
        sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
