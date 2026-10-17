import logging
from typing import Any

from core.harness import run_challenge_tests
from core.sandbox import run_code
from core.security import validate_code_safety
from models.schemas import ExecuteRequest

logger = logging.getLogger(__name__)


class ExecutionService:
    @staticmethod
    async def execute(request: ExecuteRequest) -> dict[str, Any]:
        """
        Validates learner code and runs it in the sandbox.

        Modes:
        - ``test_code`` set: learner code + challenge tests in the harness (adds ``passed``)
        - ``test_cases`` set: one sandboxed run per stdin/expected-output pair
        - otherwise: a single run with optional stdin
        """
        # 1. Static pre-check (early rejection, not the security boundary)
        is_safe, errors = validate_code_safety(request.code)
        if not is_safe:
            error_msg = "; ".join(errors)
            result = {
                "run": {
                    "stdout": "",
                    "stderr": f"Security Error: {error_msg}",
                    "code": -1,
                    "signal": None,
                    "output": f"Security Violation: {error_msg}",
                }
            }
            if request.test_code is not None:
                result["passed"] = False
            return result

        # 2. Challenge tests
        if request.test_code is not None:
            return await run_challenge_tests(request.code, request.test_code)

        # 3. Batch stdin/stdout test cases
        if request.test_cases:
            results = []
            for i, tc in enumerate(request.test_cases):
                run = await run_code(request.code, tc.input)
                passed = None
                if tc.expected_output is not None:
                    passed = run["code"] == 0 and run["stdout"].strip() == tc.expected_output.strip()
                results.append(
                    {
                        "test_case": i + 1,
                        "input": tc.input,
                        "stdout": run["stdout"],
                        "stderr": run["stderr"],
                        "code": run["code"],
                        "passed": passed,
                        "output": run["output"],
                    }
                )

            return {
                "summary": {
                    "total": len(results),
                    "passed": sum(1 for r in results if r["passed"] is True),
                    "failed": sum(1 for r in results if r["passed"] is False),
                },
                "results": results,
            }

        # 4. Single run
        return {"run": await run_code(request.code, request.stdin)}
