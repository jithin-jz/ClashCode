import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PistonExecutionService:
    """
    Service for executing Python code via the internal executor service.

    The class name is kept for compatibility with existing imports.
    """

    EXECUTOR_URL = getattr(settings, "EXECUTOR_URL", "http://executor:8011/execute")
    MAX_CODE_BYTES = int(getattr(settings, "CODE_EXECUTION_MAX_BYTES", 64 * 1024))
    TIMEOUT_SECONDS = float(getattr(settings, "CODE_EXECUTION_TIMEOUT_SECONDS", 15))

    @classmethod
    def execute_code(cls, language, code, version="*", stdin="", args=None):
        """
        Executes Python code and returns a Piston-compatible result shape.
        """
        if language.lower() not in {"python", "python3", "py"}:
            return {
                "run": {
                    "stdout": "",
                    "stderr": "Only Python execution is supported.",
                    "code": -1,
                    "signal": None,
                    "output": "Only Python execution is supported.",
                }
            }

        encoded_size = len((code or "").encode("utf-8"))
        if encoded_size > cls.MAX_CODE_BYTES:
            return {
                "run": {
                    "stdout": "",
                    "stderr": (f"Code is too large to execute. Maximum size is {cls.MAX_CODE_BYTES} bytes."),
                    "code": -1,
                    "signal": None,
                    "output": "",
                }
            }

        payload = {
            "language": "python",
            "code": code,
            "stdin": stdin,
        }

        try:
            response = requests.post(cls.EXECUTOR_URL, json=payload, timeout=cls.TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Python executor request failed: {str(e)}")
            return {
                "run": {
                    "stdout": "",
                    "stderr": f"System Error: Could not connect to Python execution engine. {str(e)}",
                    "code": -1,
                    "signal": None,
                    "output": "",
                }
            }

    @classmethod
    def run_tests(cls, language, code, test_cases, version="*"):
        """
        Runs code against a set of test cases.
        Expects test_cases to be a list of dicts with 'input' and 'expected_output'.
        """
        results = []
        all_passed = True

        for tc in test_cases:
            res = cls.execute_code(language, code, version=version, stdin=tc.get("input", ""))

            # Simple string comparison for now.
            # In a real app, you might want to strip trailing whitespace or handle precision.
            actual_output = res.get("run", {}).get("stdout", "").strip()
            expected_output = tc.get("expected_output", "").strip()

            passed = actual_output == expected_output
            if not passed:
                all_passed = False

            results.append(
                {
                    "input": tc.get("input"),
                    "expected": expected_output,
                    "actual": actual_output,
                    "passed": passed,
                    "stderr": res.get("run", {}).get("stderr", ""),
                }
            )

        return {"all_passed": all_passed, "test_results": results}
