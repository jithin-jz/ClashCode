import asyncio
import os
import time
from typing import Any

# resource module is Linux-only; gracefully degrade on Windows
try:
    import resource

    def set_resource_limits():
        """
        Sets hard limits on the execution process to prevent resource exhaustion.
        """
        # Limit CPU time (seconds)
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        # Limit memory usage (bytes) - 128MB
        resource.setrlimit(resource.RLIMIT_AS, (128 * 1024 * 1024, 128 * 1024 * 1024))
        # Limit file size creation
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))

except ImportError:
    # Windows fallback - no resource limits via preexec_fn
    set_resource_limits = None  # type: ignore


async def run_python_code(code: str, stdin: str = "") -> dict[str, Any]:
    """
    Executes Python code in an async child process with strict resource limits.
    """
    start_time = time.perf_counter()

    # Determine python executable
    python_cmd = "python" if os.name == "nt" else "python3"

    try:
        process = await asyncio.create_subprocess_exec(
            python_cmd,
            "-c",
            code,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=set_resource_limits,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(input=stdin.encode() if stdin else None),
                timeout=5.0,
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            return {
                "run": {
                    "stdout": "",
                    "stderr": "Error: Execution timed out (Limit: 5s)",
                    "code": 124,
                    "output": "Timeout",
                }
            }

        stdout = stdout_bytes.decode(errors="replace")
        stderr = stderr_bytes.decode(errors="replace")
        duration = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "run": {
                "stdout": stdout,
                "stderr": stderr,
                "code": process.returncode,
                "output": stdout if process.returncode == 0 else stderr,
                "metadata": {
                    "duration": duration,
                    "memory": "N/A",
                },
            }
        }
    except Exception as e:
        return {"run": {"stdout": "", "stderr": f"Execution Error: {str(e)}", "code": 1, "output": str(e)}}
