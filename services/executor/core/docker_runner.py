import asyncio
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict

from utils.helpers import truncate_output

logger = logging.getLogger(__name__)

# Configurable limits
TIMEOUT_SECONDS = float(os.getenv("EXECUTOR_TIMEOUT_SECONDS", "5"))
MEMORY_LIMIT_MB = int(os.getenv("EXECUTOR_MEMORY_LIMIT_MB", "128"))
CPU_LIMIT = float(os.getenv("EXECUTOR_CPU_LIMIT", "0.5"))
DOCKER_IMAGE = os.getenv("EXECUTOR_DOCKER_IMAGE", "clashcode-executor:latest")


class DockerRunner:
    @staticmethod
    async def run_code(code: str, stdin: str) -> Dict[str, Any]:
        """
        Executes code in a disposable Docker container for maximum isolation.
        """
        container_name = f"cc-exec-{uuid.uuid4().hex[:8]}"

        with tempfile.TemporaryDirectory(prefix="cc-docker-") as tmpdir:
            script_path = Path(tmpdir) / "main.py"
            script_path.write_text(code, encoding="utf-8")

            # Prepare docker run command
            # --rm: Remove container after exit
            # --network none: Disable networking
            # --memory: Limit memory
            # --cpus: Limit CPU usage
            # --name: Unique name
            # -i: Interactive (needed to pass stdin)
            # -v: Volume mount the script

            # Note: For Windows Docker Desktop, we need to be careful with paths.
            # Using absolute paths for mounting.
            abs_script_path = str(script_path.absolute())

            args = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--memory",
                f"{MEMORY_LIMIT_MB}m",
                "--cpus",
                str(CPU_LIMIT),
                "--name",
                container_name,
                "-i",
                "-v",
                f"{abs_script_path}:/home/sandbox/main.py:ro",
                DOCKER_IMAGE,
                "python3",
                "/home/sandbox/main.py",
            ]

            process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                # Write stdin and wait for completion
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(input=stdin.encode() if stdin else None),
                    timeout=TIMEOUT_SECONDS + 2.0,  # Buffer for docker overhead
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
                # Force kill the container if it's still running
                await asyncio.create_subprocess_exec(
                    "docker",
                    "kill",
                    container_name,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                return {
                    "run": {
                        "stdout": "",
                        "stderr": "Execution timed out (Docker).",
                        "code": -1,
                        "signal": "SIGKILL",
                        "output": "Execution timed out.",
                    }
                }
            except Exception as e:
                logger.error(f"Docker execution failed: {e}")
                return {
                    "run": {
                        "stdout": "",
                        "stderr": f"Internal execution error (Docker): {str(e)}",
                        "code": -1,
                        "signal": None,
                        "output": "Internal execution error.",
                    }
                }
            finally:
                # Safety check: ensure container is removed (though --rm should handle it)
                pass
