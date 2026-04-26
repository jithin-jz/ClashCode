import hmac
import json
import logging
import os
import time
from hashlib import sha256

import redis

logger = logging.getLogger(__name__)

# Constants
LEADERBOARD_CACHE_KEY = "leaderboard_data"
LEADERBOARD_CACHE_TIMEOUT = 60 * 10
AI_HINT_CACHE_TIMEOUT = 60 * 60 * 24 * 30
AI_ANALYSIS_CACHE_TIMEOUT = 60 * 60


def _publish_task_result(user_id: int, task_id: str, task_type: str, result: dict):
    """Publish task result to Redis for real-time WebSocket notification."""
    try:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        r = redis.from_url(redis_url)
        channel = f"notifications_{user_id}"
        r.publish(
            channel,
            json.dumps(
                {
                    "type": "task_completed",
                    "task_id": task_id,
                    "task_type": task_type,
                    "result": result,
                }
            ),
        )
    except Exception as e:
        logger.error(f"Failed to publish task result to Redis: {e}")


def _build_internal_headers(path: str) -> dict[str, str]:
    headers = {
        "X-Internal-API-Key": os.getenv("INTERNAL_API_KEY", ""),
        "Content-Type": "application/json",
    }
    signing_secret = os.getenv("INTERNAL_SIGNING_SECRET", "").strip()
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


def _analysis_cache_key(challenge_id: int, user_code: str) -> str:
    code_hash = sha256((user_code or "").encode("utf-8")).hexdigest()
    return f"ai_analysis:{challenge_id}:{code_hash}"
