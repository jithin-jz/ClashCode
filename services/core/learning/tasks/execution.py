import logging

from celery import shared_task
from challenges.execution import PistonExecutionService
from challenges.models import Challenge
from challenges.services import ChallengeService
from django.contrib.auth import get_user_model
from project.circuit_breaker import RedisCircuitBreaker

from .base import _publish_task_result

logger = logging.getLogger(__name__)
executor_cb = RedisCircuitBreaker("executor_service", failure_threshold=5, recovery_timeout=30)


@shared_task(bind=True)
def execute_code_task(self, user_id, challenge_id, user_code):
    """
    Execute user code against challenge test cases asynchronously.
    """
    try:
        challenge = Challenge.objects.get(id=challenge_id)
    except Challenge.DoesNotExist:
        return {"ok": False, "error": "Challenge not found"}

    if not executor_cb.is_available():
        result = {
            "ok": False,
            "error": "Execution service unavailable (Circuit Open)",
            "status_code": 503,
        }
        _publish_task_result(user_id, self.request.id, "execute", result)
        return result

    try:
        full_code = f"{user_code}\n\n{challenge.test_code}"
        execution_result = PistonExecutionService.execute_code("python", full_code)
        run_data = execution_result.get("run", {})

        exit_code = run_data.get("code", -1)
        stderr = run_data.get("stderr", "")

        payload = {
            "passed": (exit_code == 0) and not stderr,
            "stdout": run_data.get("stdout", ""),
            "stderr": stderr,
            "exit_code": exit_code,
            "output": run_data.get("output", ""),
        }

        result = {"ok": True, "payload": payload}
        executor_cb.record_success()
        _publish_task_result(user_id, self.request.id, "execute", result)
        return result
    except Exception as e:
        executor_cb.record_failure()
        logger.error(f"Code execution task failed: {e}")
        result = {"ok": False, "error": str(e), "status_code": 500}
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

    if not executor_cb.is_available():
        result = {
            "ok": False,
            "error": "Execution service unavailable (Circuit Open)",
            "status_code": 503,
        }
        _publish_task_result(user_id, self.request.id, "submit", result)
        return result

    try:
        full_code = f"{user_code}\n\n{challenge.test_code}"
        execution_result = PistonExecutionService.execute_code("python", full_code)
        run_data = execution_result.get("run", {})

        exit_code = run_data.get("code", -1)
        stderr = run_data.get("stderr", "")
        passed = (exit_code == 0) and not stderr

        if not passed:
            result = {
                "ok": False,
                "error": "Server-side validation failed.",
                "stdout": run_data.get("stdout"),
                "stderr": stderr,
                "status_code": 400,
            }
            _publish_task_result(user_id, self.request.id, "submit", result)
            return result

        # Success! Process submission
        submission_result = ChallengeService.process_submission(user, challenge, passed)
        result = {"ok": True, "payload": submission_result}
        executor_cb.record_success()
        _publish_task_result(user_id, self.request.id, "submit", result)
        return result
    except Exception as e:
        executor_cb.record_failure()
        logger.error(f"Code submission task failed: {e}")
        result = {"ok": False, "error": str(e), "status_code": 500}
        _publish_task_result(user_id, self.request.id, "submit", result)
        return result
