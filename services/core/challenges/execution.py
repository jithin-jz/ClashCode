import logging
from urllib.parse import urlparse

import requests
from django.conf import settings

from project.internal_auth import build_executor_headers

logger = logging.getLogger(__name__)


def _error_run(message: str) -> dict:
    return {
        "stdout": "",
        "stderr": message,
        "code": -1,
        "signal": None,
        "output": "",
    }


class PistonExecutionService:
    """
    Service for executing Python code via the internal executor service.

    The class name is kept for compatibility with existing imports.
    """

    EXECUTOR_URL = getattr(settings, "EXECUTOR_URL", "http://executor-service:8011/execute")
    MAX_CODE_BYTES = int(getattr(settings, "CODE_EXECUTION_MAX_BYTES", 64 * 1024))
    TIMEOUT_SECONDS = float(getattr(settings, "CODE_EXECUTION_TIMEOUT_SECONDS", 15))

    @classmethod
    def _too_large(cls, code: str) -> bool:
        return len((code or "").encode("utf-8")) > cls.MAX_CODE_BYTES

    @classmethod
    def _post(cls, payload: dict) -> dict:
        """POST to the executor with signed headers. Raises requests.RequestException on transport errors."""
        path = urlparse(cls.EXECUTOR_URL).path or "/execute"
        response = requests.post(
            cls.EXECUTOR_URL,
            json=payload,
            headers=build_executor_headers(path),
            timeout=cls.TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def execute_code(cls, language, code, version="*", stdin="", args=None):
        """
        Executes Python code and returns a Piston-compatible result shape.
        """
        if language.lower() not in {"python", "python3", "py"}:
            return {"run": _error_run("Only Python execution is supported.")}

        if cls._too_large(code):
            return {"run": _error_run(f"Code is too large to execute. Maximum size is {cls.MAX_CODE_BYTES} bytes.")}

        try:
            return cls._post({"language": "python", "code": code, "stdin": stdin})
        except requests.exceptions.RequestException as e:
            logger.error(f"Python executor request failed: {str(e)}")
            return {"run": _error_run("System Error: Could not connect to Python execution engine.")}

    @classmethod
    def run_challenge_tests(cls, code: str, test_code: str) -> dict:
        """
        Runs learner code against a challenge's tests in the executor's harness.

        Returns {"passed": bool, "run": {...}}. "passed" comes only from the
        executor's harness token, never from exit code or stderr heuristics.
        Raises requests.RequestException when the executor is unreachable so
        callers can record circuit-breaker failures.
        """
        if cls._too_large(code):
            return {
                "passed": False,
                "run": _error_run(f"Code is too large to execute. Maximum size is {cls.MAX_CODE_BYTES} bytes."),
            }

        result = cls._post({"language": "python", "code": code, "test_code": test_code or ""})
        return {"passed": result.get("passed") is True, "run": result.get("run", {})}
