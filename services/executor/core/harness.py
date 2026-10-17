"""
Challenge test harness.

Learner code and the challenge's test code run inside a trusted harness script.
A run only counts as passed when the harness prints a random per-run token after
every test finished, so ``exit()``, ``raise SystemExit``, ``os._exit(0)`` or an
empty stderr can no longer fake a pass.

The token reaches the harness over stdin and is read before learner code runs,
so it never appears in the learner's namespace. Learner code still shares the
process with the tests; see the threat model note in CLAUDE.md.
"""

import secrets
from typing import Any

from core.sandbox import run_script, to_run_payload

_HARNESS = """\
import os
import sys
import traceback

_USER_FILES = ("solution.py", "tests.py")


def _print_user_traceback(exc, stream):
    tb = exc.__traceback__
    while tb is not None and tb.tb_frame.f_code.co_filename not in _USER_FILES:
        tb = tb.tb_next
    traceback.print_exception(type(exc), exc, tb, file=stream)


def _run(path, namespace, stderr):
    with open(path, encoding="utf-8") as f:
        source = f.read()
    try:
        exec(compile(source, path, "exec"), namespace)
    except SystemExit:
        stderr.write("The program exited before the tests finished, so the run does not count.\\n")
        return False
    except BaseException as exc:
        _print_user_traceback(exc, stderr)
        return False
    return True


def main():
    token = sys.stdin.readline().strip()
    stdout, stderr = sys.stdout, sys.stderr
    namespace = {"__name__": "__main__", "__builtins__": __builtins__}
    if not (_run("solution.py", namespace, stderr) and _run("tests.py", namespace, stderr)):
        return 1
    try:
        stdout.flush()
    except Exception:
        return 1
    os.write(1, ("\\n" + token + "\\n").encode())
    return 0


raise SystemExit(main())
"""


async def run_challenge_tests(code: str, test_code: str) -> dict[str, Any]:
    """Run learner code followed by the challenge tests; ``passed`` is set by the harness token."""
    token = secrets.token_hex(16)
    result = await run_script(
        {"solution.py": code, "tests.py": test_code, "harness.py": _HARNESS},
        "harness.py",
        stdin=f"{token}\n",
    )

    marker = f"\n{token}\n"
    passed = False
    if result["returncode"] == 0 and not result["timed_out"] and result["stdout"].endswith(marker):
        passed = True
        result["stdout"] = result["stdout"][: -len(marker)]
    else:
        # Never leak a partial marker back to the learner.
        result["stdout"] = result["stdout"].replace(token, "")

    run = to_run_payload(result)
    if not passed and run["code"] == 0:
        # Exit code 0 without the token means the tests did not complete.
        run["code"] = 1
        run["output"] = run["stderr"]
    return {"run": run, "passed": passed}
