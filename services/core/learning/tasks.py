import hmac
import logging
import os
import time
from hashlib import sha256

import requests
import redis
import json

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count, Q

from challenges.models import UserProgress
from users.models import UserProfile
from project.circuit_breaker import RedisCircuitBreaker

ai_cb = RedisCircuitBreaker("ai_service", failure_threshold=3, recovery_timeout=60)

logger = logging.getLogger(__name__)
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


def build_leaderboard_data(limit: int = 100) -> list[dict[str, object]]:
    User = get_user_model()
    users = (
        User.objects.annotate(
            completed_count=Count(
                "challenge_progress",
                filter=Q(
                    challenge_progress__status=UserProgress.Status.COMPLETED,
                ),
            )
        )
        .select_related("profile")
        .filter(is_active=True, is_staff=False, is_superuser=False)
        .order_by("-profile__xp", "-completed_count", "id")[:limit]
    )

    data = []
    for user in users:
        try:
            profile = user.profile
            avatar_url = profile.avatar.url if profile.avatar else None
            xp = profile.xp
        except UserProfile.DoesNotExist:
            avatar_url = None
            xp = 0

        data.append(
            {
                "username": user.username,
                "avatar": avatar_url,
                "completed_levels": user.completed_count,
                "xp": xp,
            }
        )
    return data


@shared_task
def update_leaderboard_cache():
    """
    Periodic task to calculate and cache the leaderboard.
    Returns a summary dict stored in the Celery result backend.
    """
    logger.info("Starting leaderboard calculation task...")

    try:
        data = build_leaderboard_data()
        cache.set(LEADERBOARD_CACHE_KEY, data, timeout=LEADERBOARD_CACHE_TIMEOUT)
        logger.info("Leaderboard updated successfully.")
        return {"status": "success", "entries": len(data)}

    except Exception as e:
        logger.exception("Leaderboard task failed: %s", str(e))
        return {"status": "error", "error": str(e)}


@shared_task
def generate_ai_hint_task(
    user_id: int,
    challenge_id: int,
    challenge_slug: str,
    user_code: str,
    hint_level: int,
    user_xp: int,
):
    ai_url = os.getenv("AI_SERVICE_URL", "http://ai:8002")
    payload = {
        "user_code": user_code or "",
        "challenge_slug": challenge_slug,
        "hint_level": hint_level,
        "user_xp": user_xp,
    }
    headers = _build_internal_headers("/hints")
    cache_key = f"ai_hint:{user_id}:{challenge_id}:level:{hint_level}"

    if not ai_cb.is_available():
        logger.warning(f"Circuit Breaker OPEN for {ai_cb.name}. Aborting hint request.")
        result = {
            "ok": False,
            "error": "AI Service currently unavailable (Circuit Open)",
            "status_code": 503,
        }
        _publish_task_result(user_id, generate_ai_hint_task.request.id, "hint", result)
        return result

    try:
        resp = requests.post(
            f"{ai_url}/hints",
            json=payload,
            headers=headers,
            timeout=30,
        )
        if resp.status_code != 200:
            return {
                "ok": False,
                "error": "AI Service Error",
                "status_code": resp.status_code,
            }

        body = resp.json()
        hint_text = body.get("hint")
        if isinstance(hint_text, str) and hint_text.strip():
            cache.set(cache_key, hint_text, timeout=AI_HINT_CACHE_TIMEOUT)
        body.setdefault("hint_level", hint_level)
        body.setdefault("max_hints", 3)
        body.setdefault("max_hints", 3)
        body.setdefault("max_hints", 3)
        result = {"ok": True, "payload": body}
        ai_cb.record_success()
        _publish_task_result(user_id, generate_ai_hint_task.request.id, "hint", result)
        return result
    except requests.exceptions.RequestException as exc:
        ai_cb.record_failure()
        logger.error("AI hint task failed: %s", exc)
        result = {"ok": False, "error": "AI Service Unavailable", "status_code": 503}
        _publish_task_result(user_id, generate_ai_hint_task.request.id, "hint", result)
        return result


@shared_task(bind=True)
def generate_ai_analysis_task(
    self, user_id: int, challenge_id: int, challenge_slug: str, user_code: str
):
    ai_url = os.getenv("AI_SERVICE_URL", "http://ai:8002")
    payload = {
        "user_code": user_code or "",
        "challenge_slug": challenge_slug,
    }
    headers = _build_internal_headers("/analyze")
    cache_key = _analysis_cache_key(challenge_id, user_code)

    if not ai_cb.is_available():
        logger.warning(f"Circuit Breaker OPEN for {ai_cb.name}. Aborting analysis request.")
        result = {
            "ok": False,
            "error": "AI Service currently unavailable (Circuit Open)",
            "status_code": 503,
        }
        _publish_task_result(user_id, self.request.id, "analysis", result)
        return result

    try:
        resp = requests.post(
            f"{ai_url}/analyze",
            json=payload,
            headers=headers,
            timeout=60,
        )
        if resp.status_code != 200:
            return {
                "ok": False,
                "error": "AI Service Error",
                "status_code": resp.status_code,
            }

        body = resp.json()
        cache.set(cache_key, body, timeout=AI_ANALYSIS_CACHE_TIMEOUT)
        result = {"ok": True, "payload": body}
        ai_cb.record_success()
        _publish_task_result(user_id, self.request.id, "analysis", result)
        return result
    except requests.exceptions.RequestException as exc:
        ai_cb.record_failure()
        logger.error("AI analysis task failed: %s", exc)
        result = {"ok": False, "error": "AI Service Unavailable", "status_code": 503}
        _publish_task_result(user_id, self.request.id, "analysis", result)
        return result


@shared_task
def prewarm_ai_rag_task():
    """
    Triggers the AI service to re-index all challenges from Core.
    Ensures that the RAG vector database is up-to-date.
    """
    ai_url = os.getenv("AI_SERVICE_URL", "http://ai:8002")
    headers = _build_internal_headers("/index")
    logger.info("Triggering AI RAG pre-warming task...")

    try:
        resp = requests.post(f"{ai_url}/index", headers=headers, timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            logger.info(f"AI RAG pre-warmed successfully. Indexed {data.get('indexed_count')} challenges.")
            return {"status": "success", "data": data}
        else:
            logger.error(f"AI RAG pre-warming failed with status {resp.status_code}: {resp.text}")
            return {"status": "error", "code": resp.status_code}
    except Exception as e:
        logger.error(f"AI RAG pre-warming request failed: {e}")
        return {"status": "error", "message": str(e)}
