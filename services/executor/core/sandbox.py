"""
Sandboxed execution of untrusted Python.

Every run is a fresh interpreter process with:
- an empty environment, so no executor secret is ever inherited,
- isolated mode without site-packages or bytecode writes (``-I -S -B``),
- a private working directory that is deleted afterwards,
- CPU, address-space, file-size, file-descriptor and process rlimits (POSIX),
  applied by a trusted bootstrap before any learner code runs,
- a wall-clock timeout that kills the whole process group,
- capped stdout/stderr (the run is killed as soon as a cap is exceeded).

This is defence in depth. The real boundary is the pod/container the executor
runs in: no service-account token, no secrets other than the executor's own key,
deny-all egress, read-only root filesystem and, in production, gVisor.
"""

import asyncio
import contextlib
import os
import shutil
import signal
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from utils.helpers import OUTPUT_LIMIT_BYTES

TIMEOUT_SECONDS = float(os.getenv("EXECUTOR_TIMEOUT_SECONDS", "5"))
MEMORY_LIMIT_MB = int(os.getenv("EXECUTOR_MEMORY_LIMIT_MB", "128"))
MAX_CONCURRENT_RUNS = int(os.getenv("EXECUTOR_MAX_CONCURRENT_RUNS", "4"))
WORK_DIR = os.getenv("EXECUTOR_WORK_DIR") or None  # None -> system temp dir

_TRUNCATION_NOTE = "\n...[output truncated]"

# Runs inside the child before learner code. It applies the rlimits to its own
# process (no preexec_fn, which is unsafe with threads) and then executes the
# entrypoint script as __main__.
_BOOTSTRAP = """\
import sys
def _cc_boot():
    try:
        import resource
    except ImportError:
        resource = None
    if resource is not None:
        for name, value in {limits!r}:
            try:
                resource.setrlimit(getattr(resource, name), (value, value))
            except (ValueError, OSError):
                if sys.platform.startswith("linux"):
                    raise
    path = sys.argv[1]
    sys.argv = sys.argv[1:]
    with open(path, encoding="utf-8") as f:
        return path, f.read()
_cc_path, _cc_source = _cc_boot()
del _cc_boot
exec(compile(_cc_source, _cc_path, "exec"), {{"__name__": "__main__", "__builtins__": __builtins__}})
"""

_run_slots: asyncio.Semaphore | None = None


def _slots() -> asyncio.Semaphore:
    global _run_slots
    if _run_slots is None:
        _run_slots = asyncio.Semaphore(MAX_CONCURRENT_RUNS)
    return _run_slots


def _rlimits() -> list[tuple[str, int]]:
    cpu_seconds = max(1, int(TIMEOUT_SECONDS) + 1)
    memory_bytes = MEMORY_LIMIT_MB * 1024 * 1024
    return [
        ("RLIMIT_CPU", cpu_seconds),
        ("RLIMIT_AS", memory_bytes),
        ("RLIMIT_FSIZE", 0),  # no file writes
        ("RLIMIT_NOFILE", 64),
        ("RLIMIT_NPROC", 0),  # no fork/threads: stops fork bombs
        ("RLIMIT_CORE", 0),
    ]


def _child_env(workdir: str) -> dict[str, str]:
    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": workdir,
        "TMPDIR": workdir,
        "LANG": "C.UTF-8",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONHASHSEED": "0",
    }
    if os.name == "nt":
        # The interpreter cannot start on Windows without SYSTEMROOT (local dev only).
        env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", r"C:\Windows")
    return env


def _kill(proc: asyncio.subprocess.Process) -> None:
    with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()


async def _read_capped(stream: asyncio.StreamReader, limit: int, on_overflow) -> tuple[bytes, bool]:
    kept = bytearray()
    overflowed = False
    while True:
        chunk = await stream.read(4096)
        if not chunk:
            break
        room = limit - len(kept)
        if room > 0:
            kept.extend(chunk[:room])
        if len(chunk) > room and not overflowed:
            overflowed = True
            on_overflow()
    return bytes(kept), overflowed


async def _feed_stdin(proc: asyncio.subprocess.Process, data: bytes) -> None:
    with contextlib.suppress(BrokenPipeError, ConnectionResetError):
        if data:
            proc.stdin.write(data)
            await proc.stdin.drain()
        proc.stdin.close()


def _signal_name(returncode: int) -> str | None:
    if returncode >= 0:
        return None
    with contextlib.suppress(ValueError):
        return signal.Signals(-returncode).name
    return f"SIG{-returncode}"


async def run_script(files: dict[str, str], entrypoint: str, stdin: str = "") -> dict[str, Any]:
    """
    Write ``files`` into a fresh working directory and run ``entrypoint`` there.

    Returns raw results; callers shape them into the API response.
    """
    async with _slots():
        workdir = tempfile.mkdtemp(prefix="cc-run-", dir=WORK_DIR)
        try:
            for name, content in files.items():
                Path(workdir, name).write_text(content, encoding="utf-8")

            started = time.perf_counter()
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                "-I",
                "-S",
                "-B",
                "-c",
                _BOOTSTRAP.format(limits=_rlimits()),
                entrypoint,
                cwd=workdir,
                env=_child_env(workdir),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )

            def overflow():
                _kill(proc)

            stdin_task = asyncio.create_task(_feed_stdin(proc, stdin.encode("utf-8")))
            out_task = asyncio.create_task(_read_capped(proc.stdout, OUTPUT_LIMIT_BYTES, overflow))
            err_task = asyncio.create_task(_read_capped(proc.stderr, OUTPUT_LIMIT_BYTES, overflow))

            timed_out = False
            try:
                await asyncio.wait_for(proc.wait(), timeout=TIMEOUT_SECONDS)
            except TimeoutError:
                timed_out = True
                _kill(proc)
                await proc.wait()
            finally:
                # Learner code cannot fork (RLIMIT_NPROC), but clean up the group regardless.
                if os.name == "posix":
                    _kill(proc)

            await stdin_task
            stdout, out_truncated = await out_task
            stderr, err_truncated = await err_task

            return {
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "returncode": proc.returncode,
                "signal": _signal_name(proc.returncode),
                "timed_out": timed_out,
                "truncated": out_truncated or err_truncated,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            }
        finally:
            shutil.rmtree(workdir, ignore_errors=True)


def to_run_payload(result: dict[str, Any]) -> dict[str, Any]:
    """Shape a raw sandbox result into the Piston-compatible ``run`` payload."""
    stdout = result["stdout"]
    stderr = result["stderr"]
    code = result["returncode"]

    if result["timed_out"]:
        stderr = f"{stderr}\nExecution timed out (limit: {TIMEOUT_SECONDS:g}s).".lstrip()
        code = 124
    elif result["truncated"]:
        stdout = f"{stdout}{_TRUNCATION_NOTE}"
        stderr = f"{stderr}\nOutput limit exceeded ({OUTPUT_LIMIT_BYTES} bytes); the run was stopped.".lstrip()
    elif result["signal"] == "SIGXCPU":
        stderr = f"{stderr}\nCPU time limit exceeded.".lstrip()
    elif result["signal"] == "SIGKILL" or "MemoryError" in stderr:
        stderr = f"{stderr}\nThe program was stopped (memory or resource limit).".lstrip()

    return {
        "stdout": stdout,
        "stderr": stderr,
        "code": code,
        "signal": result["signal"],
        "output": stdout if code == 0 else stderr,
        "metadata": {"duration_ms": result["duration_ms"]},
    }


async def run_code(code: str, stdin: str = "") -> dict[str, Any]:
    """Run learner code as a plain script and return the ``run`` payload."""
    result = await run_script({"solution.py": code}, "solution.py", stdin)
    return to_run_payload(result)
