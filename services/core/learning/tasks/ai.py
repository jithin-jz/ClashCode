import logging
import os

import requests
from celery import shared_task
from django.core.cache import cache
from project.circuit_breaker import RedisCircuitBreaker

from .base import (
    AI_ANALYSIS_CACHE_TIMEOUT,
    AI_HINT_CACHE_TIMEOUT,
    _analysis_cache_key,
    _build_internal_headers,
    _publish_task_result,
)

logger = logging.getLogger(__name__)
ai_cb = RedisCircuitBreaker("ai_service", failure_threshold=3, recovery_timeout=60)


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
def generate_ai_analysis_task(self, user_id: int, challenge_id: int, challenge_slug: str, user_code: str):
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
