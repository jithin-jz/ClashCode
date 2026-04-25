import os
import re
import subprocess
import sys
import tempfile
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    import resource
except ImportError:  # pragma: no cover - resource is POSIX-only
    resource = None


MAX_CODE_BYTES = int(os.getenv("EXECUTOR_MAX_CODE_BYTES", str(64 * 1024)))
TIMEOUT_SECONDS = float(os.getenv("EXECUTOR_TIMEOUT_SECONDS", "5"))
MEMORY_LIMIT_MB = int(os.getenv("EXECUTOR_MEMORY_LIMIT_MB", "128"))
OUTPUT_LIMIT_BYTES = int(os.getenv("EXECUTOR_OUTPUT_LIMIT_BYTES", str(32 * 1024)))
BLOCK_DANGEROUS_IMPORTS = os.getenv("EXECUTOR_BLOCK_DANGEROUS_IMPORTS", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

DANGEROUS_IMPORT_PATTERN = re.compile(
    r"(^|\n)\s*(import|from)\s+"
    r"(os|subprocess|socket|shutil|pathlib|ctypes|multiprocessing|threading|asyncio|"
    r"http|urllib|requests|ftplib|telnetlib|ssl|sys)\b"
)

# Sentry initialization
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        environment=os.getenv("ENVIRONMENT", "development"),
        integrations=[FastApiIntegration()],
    )

app = FastAPI(title="CLASHCODE Python Executor", version="1.0")


class ExecuteRequest(BaseModel):
    language: str = "python"
    code: str = Field(default="", max_length=MAX_CODE_BYTES)
    stdin: str = ""


def _truncate(value: str) -> str:
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) <= OUTPUT_LIMIT_BYTES:
        return value
    truncated = encoded[:OUTPUT_LIMIT_BYTES].decode("utf-8", errors="replace")
    return f"{truncated}\n...[output truncated]"


def _limit_child_process() -> None:
    if resource is None:
        return

    memory_bytes = MEMORY_LIMIT_MB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    resource.setrlimit(resource.RLIMIT_CPU, (max(1, int(TIMEOUT_SECONDS)), max(1, int(TIMEOUT_SECONDS)) + 1))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
    if hasattr(resource, "RLIMIT_NPROC"):
        resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))


def _run_python(code: str, stdin: str) -> dict:
    code_size = len(code.encode("utf-8"))
    if code_size > MAX_CODE_BYTES:
        return {
            "run": {
                "stdout": "",
                "stderr": f"Code is too large. Maximum size is {MAX_CODE_BYTES} bytes.",
                "code": -1,
                "signal": None,
                "output": "",
            }
        }

    if BLOCK_DANGEROUS_IMPORTS and DANGEROUS_IMPORT_PATTERN.search(code):
        stderr = "Blocked import: this challenge runtime only allows safe, offline Python code."
        return {
            "run": {
                "stdout": "",
                "stderr": stderr,
                "code": -1,
                "signal": None,
                "output": stderr,
            }
        }

    with tempfile.TemporaryDirectory(prefix="clashcode-") as tmpdir:
        script_path = Path(tmpdir) / "main.py"
        script_path.write_text(code, encoding="utf-8")

        kwargs = {
            "args": [sys.executable, "-I", "-B", str(script_path)],
            "input": stdin,
            "capture_output": True,
            "text": True,
            "timeout": TIMEOUT_SECONDS,
            "cwd": tmpdir,
            "env": {
                "PYTHONIOENCODING": "utf-8",
                "PYTHONDONTWRITEBYTECODE": "1",
            },
        }
        if os.name == "posix":
            kwargs["preexec_fn"] = _limit_child_process

        try:
            completed = subprocess.run(**kwargs)
            stdout = _truncate(completed.stdout or "")
            stderr = _truncate(completed.stderr or "")
            output = _truncate(f"{stdout}{stderr}")
            return {
                "run": {
                    "stdout": stdout,
                    "stderr": stderr,
                    "code": completed.returncode,
                    "signal": None,
                    "output": output,
                }
            }
        except subprocess.TimeoutExpired as exc:
            stdout = _truncate(exc.stdout or "")
            stderr = "Execution timed out."
            return {
                "run": {
                    "stdout": stdout,
                    "stderr": stderr,
                    "code": -1,
                    "signal": "SIGKILL",
                    "output": _truncate(f"{stdout}{stderr}"),
                }
            }


@app.get("/health")
def health():
    return {"status": "ok", "service": "executor"}


@app.post("/execute")
def execute(request: ExecuteRequest):
    if request.language.lower() not in {"python", "python3", "py"}:
        raise HTTPException(status_code=400, detail="Only Python execution is supported.")

    return _run_python(request.code, request.stdin or "")
