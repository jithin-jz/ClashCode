import logging

from fastapi import APIRouter, HTTPException
from models.schemas import ExecuteRequest
from services.execution_service import ExecutionService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "executor"}


@router.post("/execute")
async def execute(request: ExecuteRequest):
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
