import logging
from typing import Dict, Any

from core.runner import run_python_code
from core.docker_runner import DockerRunner
from core.security import validate_code_safety
from models.schemas import ExecuteRequest

logger = logging.getLogger(__name__)

class ExecutionService:
    @staticmethod
    async def execute(request: ExecuteRequest) -> Dict[str, Any]:
        """
        Orchestrates code execution by validating security and selecting the appropriate runner.
        """
        # 1. Security Validation (AST)
        is_safe, errors = validate_code_safety(request.code)
        if not is_safe:
            error_msg = "; ".join(errors)
            return {
                "run": {
                    "stdout": "",
                    "stderr": f"Security Error: {error_msg}",
                    "code": -1,
                    "signal": None,
                    "output": f"Security Violation: {error_msg}",
                }
            }

        # 2. Select Runner
        if request.runner == "docker":
            return await DockerRunner.run_code(request.code, request.stdin)
        
        # Default: Host execution
        return await run_python_code(request.code, request.stdin)
