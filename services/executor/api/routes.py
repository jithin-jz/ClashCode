import logging

from fastapi import APIRouter, Depends, HTTPException

from core.auth import verify_internal_auth
from models.schemas import ExecuteRequest
from services.execution_service import ExecutionService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health():
    """Health check endpoint with Docker daemon status."""
    docker_status = "unknown"
    try:
        import docker

        client = docker.from_env()
        client.ping()
        docker_status = "connected"
    except Exception:
        docker_status = "unavailable"

    return {"status": "ok", "service": "executor", "docker": docker_status}


@router.post("/execute", dependencies=[Depends(verify_internal_auth)])
async def execute(request: ExecuteRequest):
    """
    Execute code with optional batch test cases.
    Requires internal service authentication.

    Single execution:
        {"code": "print('hello')", "stdin": "", "runner": "docker"}

    Batch test cases:
        {"code": "n = int(input())\\nprint(n*2)", "test_cases": [{"input": "5", "expected_output": "10"}]}
    """
    if request.language.lower() not in {"python", "python3", "py"}:
        raise HTTPException(status_code=400, detail="Only Python execution is supported.")

    try:
        return await ExecutionService.execute(request)
    except Exception as e:
        logger.error(f"Execution route failed: {e}")
        return {
            "run": {
                "stdout": "",
                "stderr": f"Internal Error: {str(e)}",
                "code": -1,
                "signal": None,
                "output": "Internal Error.",
            }
        }
