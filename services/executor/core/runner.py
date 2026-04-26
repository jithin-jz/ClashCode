import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

from utils.helpers import truncate_output

try:
    import resource
except ImportError:
    resource = None

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = float(os.getenv("EXECUTOR_TIMEOUT_SECONDS", "5"))
MEMORY_LIMIT_MB = int(os.getenv("EXECUTOR_MEMORY_LIMIT_MB", "128"))


def limit_child_process() -> None:
    if resource is None:
        return

    memory_bytes = MEMORY_LIMIT_MB * 1024 * 1024
    # Address space limit
    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    # CPU time limit
    cpu_limit = max(1, int(TIMEOUT_SECONDS))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit + 1))
    # File size limit (1MB)
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
    # Number of open files
    resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
    # Number of processes
    if hasattr(resource, "RLIMIT_NPROC"):
        resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))


async def run_python_code(code: str, stdin: str) -> Dict[str, Any]:
    """
    Executes Python code asynchronously in a restricted environment.
    """
    with tempfile.TemporaryDirectory(prefix="clashcode-") as tmpdir:
        script_path = Path(tmpdir) / "main.py"
        script_path.write_text(code, encoding="utf-8")

        # Command to run
        args = [sys.executable, "-I", "-B", str(script_path)]

        env = {
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PATH": os.environ.get("PATH", ""),  # Needed for sys.executable
        }

        process = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=tmpdir,
            env=env,
            preexec_fn=limit_child_process if os.name == "posix" else None,
        )

        try:
            # Write stdin and wait for completion
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(input=stdin.encode() if stdin else None),
                timeout=TIMEOUT_SECONDS + 1.0,  # Buffer for OS to kill it via resource limit
            )

            stdout = truncate_output(stdout_bytes.decode(errors="replace"))
            stderr = truncate_output(stderr_bytes.decode(errors="replace"))
            return {
                "run": {
                    "stdout": stdout,
                    "stderr": stderr,
                    "code": process.returncode,
                    "signal": None,
                    "output": truncate_output(f"{stdout}{stderr}"),
                }
            }

        except asyncio.TimeoutError:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            return {
                "run": {
                    "stdout": "",
                    "stderr": "Execution timed out.",
                    "code": -1,
                    "signal": "SIGKILL",
                    "output": "Execution timed out.",
                }
            }
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                "run": {
                    "stdout": "",
                    "stderr": "Internal execution error.",
                    "code": -1,
                    "signal": None,
                    "output": "Internal execution error.",
                }
            }
