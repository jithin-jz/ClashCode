"""HTTP client for the internal Executor service.

The Executor runs untrusted learner code in a sandbox. The AI agent uses it as
a tool so it can reason about *real* test failures instead of guessing from
static code.
"""

import logging

import httpx
from config import settings

from core.security import build_executor_headers

logger = logging.getLogger(__name__)

# Trim very long program output before it ever reaches the LLM context window.
_MAX_STREAM_CHARS = 4000


def _truncate(text: str, limit: int = _MAX_STREAM_CHARS) -> str:
    if text and len(text) > limit:
        return text[:limit] + "\n... [output truncated]"
    return text or ""


async def run_tests_in_sandbox(user_code: str, test_code: str) -> dict:
    """Run learner code against the challenge tests in the executor's harness.

    Returns a dict shaped like:
        {"ok": bool, "passed": bool, "stdout": str, "stderr": str, "exit_code": int}
    On transport failure ``ok`` is False and ``stderr`` explains why.
    """
    path = "/execute"
    url = f"{settings.EXECUTOR_SERVICE_URL.rstrip('/')}{path}"
    headers = build_executor_headers(path)
    payload = {"language": "python", "code": user_code, "test_code": test_code}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=30)
    except httpx.RequestError as exc:
        logger.error("Executor connection failed: %s", exc)
        return {"ok": False, "passed": False, "stdout": "", "stderr": "Executor service unavailable.", "exit_code": -1}

    if resp.status_code != 200:
        logger.error("Executor returned %s: %s", resp.status_code, resp.text)
        return {
            "ok": False,
            "passed": False,
            "stdout": "",
            "stderr": f"Executor returned status {resp.status_code}.",
            "exit_code": -1,
        }

    body = resp.json()
    run = body.get("run", {})
    return {
        "ok": True,
        "passed": body.get("passed") is True,
        "stdout": _truncate(run.get("stdout", "")),
        "stderr": _truncate(run.get("stderr", "")),
        "exit_code": run.get("code", -1),
    }
