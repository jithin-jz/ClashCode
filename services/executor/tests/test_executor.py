import hmac
import sys
import time
from hashlib import sha256

import pytest
from httpx import ASGITransport, AsyncClient
from main import app

from core import sandbox
from core.harness import run_challenge_tests
from core.security import validate_code_safety

linux_only = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="rlimits are enforced on Linux")


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def _execute(client, **payload):
    resp = await client.post("/execute", json=payload)
    assert resp.status_code == 200
    return resp.json()


# --- Basic execution ---


async def test_health(client):
    """Health endpoint returns OK."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "executor"


async def test_execute_simple(client):
    data = await _execute(client, code="print('hello world')")
    assert data["run"]["stdout"].strip() == "hello world"
    assert data["run"]["code"] == 0


async def test_execute_with_stdin(client):
    data = await _execute(client, code="name = input()\nprint(f'hi {name}')", stdin="Alice")
    assert data["run"]["stdout"].strip() == "hi Alice"


async def test_execute_syntax_error(client):
    data = await _execute(client, code="def foo(\n")
    assert data["run"]["code"] == -1
    assert "Syntax Error" in data["run"]["stderr"]


async def test_execute_runtime_error(client):
    data = await _execute(client, code="x = 1 / 0")
    assert data["run"]["code"] != 0
    assert "ZeroDivisionError" in data["run"]["stderr"]


async def test_unsupported_language(client):
    resp = await client.post("/execute", json={"code": "console.log('hi')", "language": "javascript"})
    assert resp.status_code == 400


async def test_legacy_runner_field_is_ignored(client):
    data = await _execute(client, code="print(2 + 2)", runner="host")
    assert data["run"]["stdout"].strip() == "4"


# --- Static pre-check ---


@pytest.mark.parametrize(
    "code",
    [
        "import os\nos.system('ls')",
        "import subprocess\nsubprocess.run(['ls'])",
        "eval('1+1')",
        "x = ''.__class__.__subclasses__()",
        "print(__import__('os').environ)",
        "__import__('subprocess').run(['id'])",
        "import importlib\nimportlib.import_module('o' + 's')",
        "import io\nprint(io.open('/etc/passwd').read())",
        "import builtins\nbuiltins.open('/etc/passwd')",
        "__builtins__['open']('/etc/passwd')",
        "try:\n    1/0\nexcept Exception as e:\n    print(e.__traceback__.tb_frame.f_back.f_locals)",
        "exit()",
        "quit()",
        "import gc\ngc.get_objects()",
    ],
)
def test_security_precheck_blocks(code):
    is_safe, errors = validate_code_safety(code)
    assert not is_safe, f"expected to be blocked: {code!r}"
    assert errors


@pytest.mark.parametrize(
    "code",
    [
        "from collections import Counter\nprint(Counter('aab'))",
        "import math, re, json, statistics\nprint(math.sqrt(4))",
        "from itertools import permutations\nfrom functools import reduce\nfrom datetime import date",
        "class A:\n    def __init__(self):\n        self.x = 1\nprint(A().x)",
    ],
)
def test_security_precheck_allows_normal_code(code):
    is_safe, errors = validate_code_safety(code)
    assert is_safe, errors


async def test_blocked_code_is_rejected_via_api(client):
    data = await _execute(client, code="print(__import__('os').environ)")
    assert data["run"]["code"] == -1
    assert "Security Error" in data["run"]["stderr"]


# --- Sandbox isolation (bypasses the pre-check on purpose) ---


async def test_sandbox_does_not_inherit_secrets(monkeypatch):
    monkeypatch.setenv("SUPER_SECRET_TOKEN", "do-not-leak")
    result = await sandbox.run_script({"main.py": "import os\nprint(sorted(os.environ))"}, "main.py")
    assert result["returncode"] == 0
    assert "SUPER_SECRET_TOKEN" not in result["stdout"]
    assert "do-not-leak" not in result["stdout"]


async def test_sandbox_timeout(monkeypatch):
    monkeypatch.setattr(sandbox, "TIMEOUT_SECONDS", 1)
    started = time.monotonic()
    run = await sandbox.run_code("while True:\n    pass")
    assert time.monotonic() - started < 10
    assert run["code"] != 0
    assert "limit" in run["stderr"].lower()


async def test_sandbox_output_is_capped(monkeypatch):
    monkeypatch.setattr(sandbox, "OUTPUT_LIMIT_BYTES", 1024)
    run = await sandbox.run_code("while True:\n    print('x' * 100)")
    assert len(run["stdout"]) < 2048
    assert "output truncated" in run["stdout"]
    assert "Output limit exceeded" in run["stderr"]


async def test_sandbox_workdir_is_removed():
    result = await sandbox.run_script({"main.py": "import os\nprint(os.getcwd())"}, "main.py")
    workdir = result["stdout"].strip()
    import os

    assert workdir
    assert not os.path.exists(workdir)


@linux_only
async def test_sandbox_blocks_fork():
    result = await sandbox.run_script({"main.py": "import os\nos.fork()\nprint('forked')"}, "main.py")
    assert result["returncode"] != 0
    assert "forked" not in result["stdout"]


@linux_only
async def test_sandbox_memory_limit():
    result = await sandbox.run_script({"main.py": "x = bytearray(1024 * 1024 * 1024)\nprint('allocated')"}, "main.py")
    assert result["returncode"] != 0
    assert "allocated" not in result["stdout"]


@linux_only
async def test_sandbox_cannot_write_files():
    result = await sandbox.run_script({"main.py": "open('out.txt', 'w').write('x' * 10)\nprint('wrote')"}, "main.py")
    assert result["returncode"] != 0


# --- Challenge test harness ---

TESTS = 'assert say_hello() == "Hello, Python!"'


async def test_harness_passes_correct_solution():
    result = await run_challenge_tests('def say_hello():\n    return "Hello, Python!"', TESTS)
    assert result["passed"] is True
    assert result["run"]["code"] == 0


async def test_harness_fails_wrong_solution():
    result = await run_challenge_tests('def say_hello():\n    return "nope"', TESTS)
    assert result["passed"] is False
    assert "AssertionError" in result["run"]["stderr"]


async def test_harness_keeps_learner_output_but_hides_token():
    result = await run_challenge_tests('print("debug")\ndef say_hello():\n    return "Hello, Python!"', TESTS)
    assert result["passed"] is True
    assert result["run"]["stdout"].strip() == "debug"


@pytest.mark.parametrize(
    "cheat",
    [
        "raise SystemExit(0)",
        "import os\nos._exit(0)",
        "import sys\nsys.exit(0)",
        "def say_hello():\n    raise SystemExit(0)",
        "import sys\nsys.stdout.write('\\n' + 'a' * 32 + '\\n')\nraise SystemExit(0)",
    ],
)
async def test_harness_rejects_early_exit(cheat):
    # Called directly so the static pre-check does not hide the harness behaviour.
    result = await run_challenge_tests(cheat, TESTS)
    assert result["passed"] is False
    assert result["run"]["code"] != 0


async def test_harness_via_api(client):
    data = await _execute(client, code='def say_hello():\n    return "Hello, Python!"', test_code=TESTS)
    assert data["passed"] is True

    data = await _execute(client, code="exit()", test_code=TESTS)
    assert data["passed"] is False


# --- Batch stdin/stdout cases ---


async def test_batch_test_cases(client):
    data = await _execute(
        client,
        code="n = int(input())\nprint(n ** 2)",
        test_cases=[
            {"input": "2", "expected_output": "4"},
            {"input": "3", "expected_output": "9"},
            {"input": "0", "expected_output": "0"},
        ],
    )
    assert data["summary"] == {"total": 3, "passed": 3, "failed": 0}


async def test_batch_with_failure(client):
    data = await _execute(
        client,
        code="n = int(input())\nprint(n + 1)",
        test_cases=[
            {"input": "1", "expected_output": "2"},
            {"input": "2", "expected_output": "5"},
        ],
    )
    assert data["summary"]["passed"] == 1
    assert data["summary"]["failed"] == 1
    assert data["results"][1]["passed"] is False


async def test_batch_no_expected_output(client):
    data = await _execute(client, code="print(input().upper())", test_cases=[{"input": "hello"}])
    assert data["results"][0]["stdout"].strip() == "HELLO"
    assert data["results"][0]["passed"] is None


# --- Authentication ---


def _signed_headers(key: str, secret: str, path: str = "/execute", ts: int | None = None) -> dict:
    timestamp = str(ts if ts is not None else int(time.time()))
    signature = hmac.new(secret.encode(), f"{timestamp}:{path}".encode(), sha256).hexdigest()
    return {"X-Internal-API-Key": key, "X-Internal-Timestamp": timestamp, "X-Internal-Signature": signature}


@pytest.fixture
def auth_enabled(monkeypatch):
    monkeypatch.setenv("EXECUTOR_ALLOW_UNAUTHENTICATED", "false")
    monkeypatch.setenv("EXECUTOR_API_KEY", "exec-key")
    monkeypatch.setenv("EXECUTOR_SIGNING_SECRET", "exec-secret")
    monkeypatch.delenv("INTERNAL_REQUIRE_SIGNATURE", raising=False)


async def test_auth_rejects_missing_key(client, auth_enabled):
    resp = await client.post("/execute", json={"code": "print(1)"})
    assert resp.status_code == 401


async def test_auth_rejects_bad_signature(client, auth_enabled):
    headers = _signed_headers("exec-key", "wrong-secret")
    resp = await client.post("/execute", json={"code": "print(1)"}, headers=headers)
    assert resp.status_code == 401


async def test_auth_rejects_stale_timestamp(client, auth_enabled):
    headers = _signed_headers("exec-key", "exec-secret", ts=int(time.time()) - 3600)
    resp = await client.post("/execute", json={"code": "print(1)"}, headers=headers)
    assert resp.status_code == 401


async def test_auth_accepts_valid_signature(client, auth_enabled):
    headers = _signed_headers("exec-key", "exec-secret")
    resp = await client.post("/execute", json={"code": "print(1)"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["run"]["stdout"].strip() == "1"


async def test_auth_fails_closed_without_key(client, monkeypatch):
    monkeypatch.setenv("EXECUTOR_ALLOW_UNAUTHENTICATED", "false")
    monkeypatch.setenv("EXECUTOR_API_KEY", "")
    monkeypatch.setenv("INTERNAL_API_KEY", "")
    resp = await client.post("/execute", json={"code": "print(1)"})
    health = await client.get("/health")
    assert resp.status_code == 503
    assert health.json()["auth"] == "misconfigured"
