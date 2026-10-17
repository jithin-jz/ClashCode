import json
import logging
import os
from hashlib import sha256

import redis

from project.internal_auth import build_internal_headers

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
    return build_internal_headers(path)


def _analysis_cache_key(challenge_id: int, user_code: str) -> str:
    code_hash = sha256((user_code or "").encode("utf-8")).hexdigest()
    return f"ai_analysis:{challenge_id}:{code_hash}"
