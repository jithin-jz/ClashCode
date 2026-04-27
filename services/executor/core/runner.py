import resource
import time
import subprocess
from typing import Any, Dict

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

async def run_python_code(code: str, stdin: str = "") -> Dict[str, Any]:
    """
    Executes Python code in a child process with strict resource limits.
    """
    start_time = time.perf_counter()
    
    try:
        process = subprocess.Popen(
            ["python3", "-c", code],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=set_resource_limits
        )

        stdout, stderr = process.communicate(input=stdin, timeout=5)
        duration = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "run": {
                "stdout": stdout,
                "stderr": stderr,
                "code": process.returncode,
                "output": stdout if process.returncode == 0 else stderr,
                "metadata": {
                    "duration": duration,
                    "memory": "N/A" # Accurate child memory tracking requires more complex syscalls in Python
                }
            }
        }
    except subprocess.TimeoutExpired:
        return {
            "run": {
                "stdout": "",
                "stderr": "Error: Execution timed out (Limit: 5s)",
                "code": 124,
                "output": "Timeout"
            }
        }
    except Exception as e:
        return {
            "run": {
                "stdout": "",
                "stderr": f"Execution Error: {str(e)}",
                "code": 1,
                "output": str(e)
            }
        }
