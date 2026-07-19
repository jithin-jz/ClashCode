import contextlib
import json
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

import docker
from docker.errors import DockerException, NotFound

from utils.helpers import truncate_output

logger = logging.getLogger(__name__)

# Configurable limits
TIMEOUT_SECONDS = float(os.getenv("EXECUTOR_TIMEOUT_SECONDS", "5"))
MEMORY_LIMIT_MB = int(os.getenv("EXECUTOR_MEMORY_LIMIT_MB", "128"))
CPU_LIMIT = float(os.getenv("EXECUTOR_CPU_LIMIT", "0.5"))
DOCKER_IMAGE = os.getenv("EXECUTOR_DOCKER_IMAGE", "python:3.12-slim")


def _get_docker_client() -> docker.DockerClient:
    """Create a Docker client from environment."""
    return docker.from_env()


class DockerRunner:
    @staticmethod
    async def run_code(code: str, stdin: str = "") -> dict[str, Any]:
        """
        Executes code in a disposable Docker container using the Docker SDK.
        Stdin is passed via a file mount to avoid platform-specific socket issues.
        """
        container = None
        container_name = f"cc-exec-{uuid.uuid4().hex[:8]}"

        try:
            client = _get_docker_client()

            with tempfile.TemporaryDirectory(prefix="cc-docker-") as tmpdir:
                # Write user code wrapped with stdin redirection
                if stdin:
                    # Wrap the user's code to read stdin from a file
                    wrapper = "import sys, io\n" "sys.stdin = open('/home/sandbox/stdin.txt', 'r')\n"
                    full_code = wrapper + code
                    stdin_path = Path(tmpdir) / "stdin.txt"
                    stdin_path.write_text(stdin, encoding="utf-8")
                else:
                    full_code = code
                    stdin_path = None

                script_path = Path(tmpdir) / "main.py"
                script_path.write_text(full_code, encoding="utf-8")

                # Build volume mounts
                volumes = {
                    str(script_path.absolute()): {
                        "bind": "/home/sandbox/main.py",
                        "mode": "ro",
                    }
                }
                if stdin_path:
                    volumes[str(stdin_path.absolute())] = {
                        "bind": "/home/sandbox/stdin.txt",
                        "mode": "ro",
                    }

                # Run container with strict isolation
                container = client.containers.run(
                    image=DOCKER_IMAGE,
                    command=["python3", "/home/sandbox/main.py"],
                    name=container_name,
                    detach=True,
                    network_mode="none",
                    mem_limit=f"{MEMORY_LIMIT_MB}m",
                    nano_cpus=int(CPU_LIMIT * 1e9),
                    volumes=volumes,
                    user="nobody",
                    read_only=True,
                    tmpfs={"/tmp": "size=16m,noexec"},
                )

                # Wait for container to finish with timeout
                result = container.wait(timeout=TIMEOUT_SECONDS + 2)
                exit_code = result.get("StatusCode", -1)

                stdout = container.logs(stdout=True, stderr=False).decode(errors="replace")
                stderr = container.logs(stdout=False, stderr=True).decode(errors="replace")

                stdout = truncate_output(stdout)
                stderr = truncate_output(stderr)

                return {
                    "run": {
                        "stdout": stdout,
                        "stderr": stderr,
                        "code": exit_code,
                        "signal": None,
                        "output": truncate_output(f"{stdout}{stderr}"),
                    }
                }

        except Exception as e:
            error_msg = str(e)
            if "timed out" in error_msg.lower() or "read timeout" in error_msg.lower():
                return {
                    "run": {
                        "stdout": "",
                        "stderr": "Execution timed out.",
                        "code": -1,
                        "signal": "SIGKILL",
                        "output": "Execution timed out.",
                    }
                }
            logger.error(f"Docker execution failed: {e}")
            return {
                "run": {
                    "stdout": "",
                    "stderr": f"Execution error: {error_msg}",
                    "code": -1,
                    "signal": None,
                    "output": "Internal execution error.",
                }
            }
        finally:
            # Cleanup container
            if container:
                with contextlib.suppress(NotFound, DockerException):
                    container.remove(force=True)

    @staticmethod
    async def run_batch(code: str, test_cases: list[dict[str, str]]) -> list[dict[str, Any]]:
        """
        Executes code against multiple test cases in a single container.
        Uses a wrapper script that iterates over inputs.
        """
        container = None
        container_name = f"cc-batch-{uuid.uuid4().hex[:8]}"
        results = []

        try:
            client = _get_docker_client()

            with tempfile.TemporaryDirectory(prefix="cc-batch-") as tmpdir:
                # Write the user's code
                script_path = Path(tmpdir) / "solution.py"
                script_path.write_text(code, encoding="utf-8")

                # Write test inputs as JSON for the runner to consume
                inputs_data = [tc.get("input", "") for tc in test_cases]
                inputs_path = Path(tmpdir) / "inputs.json"
                inputs_path.write_text(json.dumps(inputs_data), encoding="utf-8")

                # Write the batch runner script
                runner_code = """
import json
import sys
import io
import traceback

# Load inputs
with open("/home/sandbox/inputs.json", "r") as f:
    inputs = json.load(f)

results = []
for test_input in inputs:
    old_stdin = sys.stdin
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    sys.stdin = io.StringIO(test_input)
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    sys.stdout = captured_stdout
    sys.stderr = captured_stderr

    exit_code = 0
    try:
        with open("/home/sandbox/solution.py", "r") as f:
            solution_code = f.read()
        exec(compile(solution_code, "solution.py", "exec"), {"__builtins__": __builtins__})
    except SystemExit as e:
        exit_code = e.code if e.code else 0
    except Exception:
        captured_stderr.write(traceback.format_exc())
        exit_code = 1
    finally:
        sys.stdin = old_stdin
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    results.append({
        "stdout": captured_stdout.getvalue(),
        "stderr": captured_stderr.getvalue(),
        "code": exit_code,
    })

# Output results as JSON to stdout
print(json.dumps(results))
"""
                runner_path = Path(tmpdir) / "runner.py"
                runner_path.write_text(runner_code, encoding="utf-8")

                # Calculate timeout: base + per test case
                total_timeout = TIMEOUT_SECONDS * len(test_cases) + 5

                container = client.containers.run(
                    image=DOCKER_IMAGE,
                    command=["python3", "/home/sandbox/runner.py"],
                    name=container_name,
                    detach=True,
                    network_mode="none",
                    mem_limit=f"{MEMORY_LIMIT_MB}m",
                    nano_cpus=int(CPU_LIMIT * 1e9),
                    volumes={
                        str(script_path.absolute()): {
                            "bind": "/home/sandbox/solution.py",
                            "mode": "ro",
                        },
                        str(inputs_path.absolute()): {
                            "bind": "/home/sandbox/inputs.json",
                            "mode": "ro",
                        },
                        str(runner_path.absolute()): {
                            "bind": "/home/sandbox/runner.py",
                            "mode": "ro",
                        },
                    },
                    user="nobody",
                    read_only=True,
                    tmpfs={"/tmp": "size=16m,noexec"},
                )

                result = container.wait(timeout=total_timeout)
                exit_code = result.get("StatusCode", -1)

                stdout = container.logs(stdout=True, stderr=False).decode(errors="replace")
                stderr = container.logs(stdout=False, stderr=True).decode(errors="replace")

                if exit_code == 0 and stdout.strip():
                    batch_results = json.loads(stdout.strip())
                    for i, tc in enumerate(test_cases):
                        r = batch_results[i] if i < len(batch_results) else {}
                        tc_stdout = truncate_output(r.get("stdout", ""))
                        tc_stderr = truncate_output(r.get("stderr", ""))
                        tc_code = r.get("code", -1)

                        # Check expected output if provided
                        passed = None
                        expected = tc.get("expected_output")
                        if expected is not None:
                            passed = tc_stdout.strip() == expected.strip()

                        results.append(
                            {
                                "test_case": i + 1,
                                "input": tc.get("input", ""),
                                "stdout": tc_stdout,
                                "stderr": tc_stderr,
                                "code": tc_code,
                                "passed": passed,
                                "output": tc_stdout if tc_code == 0 else tc_stderr,
                            }
                        )
                else:
                    # Runner itself failed
                    error = truncate_output(stderr or stdout)
                    for i, tc in enumerate(test_cases):
                        results.append(
                            {
                                "test_case": i + 1,
                                "input": tc.get("input", ""),
                                "stdout": "",
                                "stderr": error,
                                "code": -1,
                                "passed": False,
                                "output": error,
                            }
                        )

        except Exception as e:
            error_msg = str(e)
            if "timed out" in error_msg.lower() or "read timeout" in error_msg.lower():
                for i, tc in enumerate(test_cases):
                    results.append(
                        {
                            "test_case": i + 1,
                            "input": tc.get("input", ""),
                            "stdout": "",
                            "stderr": "Execution timed out.",
                            "code": -1,
                            "passed": False,
                            "output": "Execution timed out.",
                        }
                    )
            else:
                logger.error(f"Docker batch execution failed: {e}")
                for i, tc in enumerate(test_cases):
                    results.append(
                        {
                            "test_case": i + 1,
                            "input": tc.get("input", ""),
                            "stdout": "",
                            "stderr": f"Execution error: {error_msg}",
                            "code": -1,
                            "passed": False,
                            "output": "Internal execution error.",
                        }
                    )
        finally:
            if container:
                with contextlib.suppress(NotFound, DockerException):
                    container.remove(force=True)

        return results
