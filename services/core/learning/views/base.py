import logging
from hashlib import sha256

from celery.result import AsyncResult
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)
AI_TASK_META_TIMEOUT = 60 * 60 * 24


def _analysis_cache_key(challenge_id: int, user_code: str) -> str:
    code_hash = sha256((user_code or "").encode("utf-8")).hexdigest()
    return f"ai_analysis:{challenge_id}:{code_hash}"


def _task_meta_cache_key(task_id: str) -> str:
    return f"ai_task_meta:{task_id}"


def _store_ai_task_meta(task_id: str, user_id: int, task_type: str) -> None:
    cache.set(
        _task_meta_cache_key(task_id),
        {"user_id": user_id, "task_type": task_type},
        timeout=AI_TASK_META_TIMEOUT,
    )


def _task_status_label(async_result: AsyncResult) -> str:
    if async_result.status in {"PENDING", "RECEIVED"}:
        return "queued"
    if async_result.status == "STARTED":
        return "processing"
    if async_result.status == "SUCCESS":
        return "success"
    if async_result.status in {"FAILURE", "REVOKED"}:
        return "failed"
    return async_result.status.lower()


def _build_ai_result_response(task_result: dict) -> Response:
    if not task_result or not isinstance(task_result, dict):
        return Response(
            {"error": "AI task returned invalid result"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if not task_result.get("ok"):
        return Response(
            {"error": task_result.get("error", "AI generation failed")},
            status=task_result.get("status_code", status.HTTP_503_SERVICE_UNAVAILABLE),
        )

    return Response(task_result.get("payload", {}), status=status.HTTP_200_OK)
