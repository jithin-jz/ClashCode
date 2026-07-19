from __future__ import annotations

import hmac
import os
import time
from hashlib import sha256

from django.conf import settings


def _timing_safe_equal(left: str, right: str) -> bool:
    return hmac.compare_digest((left or "").strip(), (right or "").strip())


def authorize_internal_request(request) -> bool:
    """
    Authorize internal service-to-service requests.

    Base requirement:
    - X-Internal-API-Key matches INTERNAL_API_KEY.

    Hardened mode:
    - Production requires INTERNAL_SIGNING_SECRET unless INTERNAL_REQUIRE_SIGNATURE=False.
    - Sender must provide:
      - X-Internal-Timestamp (unix seconds)
      - X-Internal-Signature (HMAC_SHA256 over "<timestamp>:<path>")
    """
    internal_key = os.getenv("INTERNAL_API_KEY", "").strip()
    request_key = request.headers.get("X-Internal-API-Key", "").strip()

    if not internal_key or not _timing_safe_equal(request_key, internal_key):
        return False

    signing_secret = os.getenv("INTERNAL_SIGNING_SECRET", "").strip()
    if not signing_secret:
        return not getattr(settings, "INTERNAL_REQUIRE_SIGNATURE", True)

    timestamp = request.headers.get("X-Internal-Timestamp", "").strip()
    signature = request.headers.get("X-Internal-Signature", "").strip()
    if not timestamp or not signature:
        return False

    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False

    now = int(time.time())
    max_skew = 120
    if abs(now - ts) > max_skew:
        return False

    message = f"{timestamp}:{request.path}"
    expected = hmac.HMAC(
        signing_secret.encode("utf-8"),
        message.encode("utf-8"),
        sha256,
    ).hexdigest()
    return _timing_safe_equal(signature, expected)
