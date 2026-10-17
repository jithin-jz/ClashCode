import logging

from fastapi import APIRouter, Depends, HTTPException

from core.auth import auth_configuration_error, verify_internal_auth
from models.schemas import ExecuteRequest
from services.execution_service import ExecutionService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health():
    """Liveness/readiness: the process is up and its auth is usable."""
    auth_ok = auth_configuration_error() is None
    return {"status": "ok", "service": "executor", "auth": "configured" if auth_ok else "misconfigured"}


@router.post("/execute", dependencies=[Depends(verify_internal_auth)])
async def execute(request: ExecuteRequest):
    """
    Execute learner code. Requires internal service authentication.

    Single run:
        {"code": "print('hello')", "stdin": ""}

    Challenge tests (harness decides "passed"):
        {"code": "def f(): return 1", "test_code": "assert f() == 1"}

    Batch stdin/stdout cases:
        {"code": "n = int(input())\\nprint(n*2)", "test_cases": [{"input": "5", "expected_output": "10"}]}
    """
    if request.language.lower() not in {"python", "python3", "py"}:
        raise HTTPException(status_code=400, detail="Only Python execution is supported.")

    try:
        return await ExecutionService.execute(request)
    except Exception:
        logger.exception("Execution route failed")
        result = {
            "run": {
                "stdout": "",
                "stderr": "Internal execution error.",
                "code": -1,
                "signal": None,
                "output": "Internal execution error.",
            }
        }
        if request.test_code is not None:
            result["passed"] = False
        return result
