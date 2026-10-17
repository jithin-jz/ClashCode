import logging

import requests
from celery import shared_task
from django.contrib.auth import get_user_model

from challenges.execution import PistonExecutionService
from challenges.models import Challenge
from challenges.services import ChallengeService
from project.circuit_breaker import RedisCircuitBreaker

from .base import _publish_task_result

logger = logging.getLogger(__name__)
executor_cb = RedisCircuitBreaker("executor_service", failure_threshold=5, recovery_timeout=30)

_EXECUTOR_UNAVAILABLE = {
    "ok": False,
    "error": "Execution service unavailable. Please try again shortly.",
    "status_code": 503,
}


def _run_tests(task, user_id: int, task_type: str, challenge: Challenge, user_code: str):
    """Run the challenge harness, handling the circuit breaker. Returns (result_or_none, error_result)."""
    if not executor_cb.is_available():
        result = {**_EXECUTOR_UNAVAILABLE, "error": "Execution service unavailable (Circuit Open)"}
        _publish_task_result(user_id, task.request.id, task_type, result)
        return None, result

    try:
        outcome = PistonExecutionService.run_challenge_tests(user_code, challenge.test_code)
    except requests.exceptions.RequestException as e:
        executor_cb.record_failure()
        logger.error(f"Executor request failed for {task_type}: {e}")
        _publish_task_result(user_id, task.request.id, task_type, _EXECUTOR_UNAVAILABLE)
        return None, _EXECUTOR_UNAVAILABLE

    executor_cb.record_success()
    return outcome, None


@shared_task(bind=True)
def execute_code_task(self, user_id, challenge_id, user_code):
    """
    Execute user code against challenge test cases asynchronously.
    """
    try:
        challenge = Challenge.objects.get(id=challenge_id)
    except Challenge.DoesNotExist:
        return {"ok": False, "error": "Challenge not found"}

    try:
        outcome, error = _run_tests(self, user_id, "execute", challenge, user_code)
        if error:
            return error

        run_data = outcome["run"]
        payload = {
            "passed": outcome["passed"],
            "stdout": run_data.get("stdout", ""),
            "stderr": run_data.get("stderr", ""),
            "exit_code": run_data.get("code", -1),
            "output": run_data.get("output", ""),
        }

        result = {"ok": True, "payload": payload}
        _publish_task_result(user_id, self.request.id, "execute", result)
        return result
    except Exception:
        logger.exception("Code execution task failed")
        result = {"ok": False, "error": "Code execution failed.", "status_code": 500}
        _publish_task_result(user_id, self.request.id, "execute", result)
        return result


@shared_task(bind=True)
def submit_code_task(self, user_id, challenge_id, user_code):
    """
    Submit user code for validation and progress update.
    """
    User = get_user_model()
    try:
        challenge = Challenge.objects.get(id=challenge_id)
        user = User.objects.get(id=user_id)
    except (Challenge.DoesNotExist, User.DoesNotExist):
        return {"ok": False, "error": "Challenge or User not found"}

    if not ChallengeService.is_unlocked(user, challenge):
        result = {"ok": False, "error": "This level is locked.", "status_code": 403}
        _publish_task_result(user_id, self.request.id, "submit", result)
        return result

    try:
        outcome, error = _run_tests(self, user_id, "submit", challenge, user_code)
        if error:
            return error

        run_data = outcome["run"]
        if not outcome["passed"]:
            result = {
                "ok": False,
                "error": "Server-side validation failed.",
                "stdout": run_data.get("stdout"),
                "stderr": run_data.get("stderr", ""),
                "status_code": 400,
            }
            _publish_task_result(user_id, self.request.id, "submit", result)
            return result

        # Cache user code for GitHub sync signal to pick up
        from django.core.cache import cache

        cache.set(
            f"github_sync:last_code:{user_id}:{challenge_id}",
            user_code,
            timeout=300,  # 5 min TTL — plenty for the signal to fire
        )

        # Success! Process submission
        submission_result = ChallengeService.process_submission(user, challenge, True)
        result = {"ok": True, "payload": submission_result}
        _publish_task_result(user_id, self.request.id, "submit", result)
        return result
    except Exception:
        logger.exception("Code submission task failed")
        result = {"ok": False, "error": "Code submission failed.", "status_code": 500}
        _publish_task_result(user_id, self.request.id, "submit", result)
        return result
