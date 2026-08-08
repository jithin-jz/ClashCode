"""HTTP client for the internal Executor service.

The Executor runs untrusted learner code inside network-isolated, non-root
Docker containers. The AI agent uses it as a tool so it can reason about *real*
test failures instead of guessing from static code.
"""

import logging

import httpx
from config import settings

from core.security import build_internal_headers

logger = logging.getLogger(__name__)

# Trim very long program output before it ever reaches the LLM context window.
_MAX_STREAM_CHARS = 4000


def _truncate(text: str, limit: int = _MAX_STREAM_CHARS) -> str:
    if text and len(text) > limit:
        return text[:limit] + "\n... [output truncated]"
    return text or ""


async def run_code_in_sandbox(full_code: str) -> dict:
    """Execute Python code in the sandboxed executor and return a normalized result.

    Returns a dict shaped like:
        {"ok": bool, "stdout": str, "stderr": str, "exit_code": int}
    On transport failure ``ok`` is False and ``stderr`` explains why.
    """
    path = "/execute"
    url = f"{settings.EXECUTOR_SERVICE_URL.rstrip('/')}{path}"
    headers = build_internal_headers(path)
    payload = {"language": "python", "code": full_code, "runner": "docker"}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=30)
    except httpx.RequestError as exc:
        logger.error("Executor connection failed: %s", exc)
        return {"ok": False, "stdout": "", "stderr": "Executor service unavailable.", "exit_code": -1}

    if resp.status_code != 200:
        logger.error("Executor returned %s: %s", resp.status_code, resp.text)
        return {
            "ok": False,
            "stdout": "",
            "stderr": f"Executor returned status {resp.status_code}.",
            "exit_code": -1,
        }

    run = resp.json().get("run", {})
    exit_code = run.get("code", -1)
    stderr = _truncate(run.get("stderr", ""))
    return {
        "ok": True,
        "stdout": _truncate(run.get("stdout", "")),
        "stderr": stderr,
        "exit_code": exit_code,
    }
