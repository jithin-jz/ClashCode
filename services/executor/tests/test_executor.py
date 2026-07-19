import pytest
from httpx import ASGITransport, AsyncClient
from main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    """Health endpoint returns OK."""
    async with client as ac:
        resp = await ac.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "executor"


@pytest.mark.asyncio
async def test_execute_simple_host(client):
    """Simple print statement executes on host runner."""
    async with client as ac:
        resp = await ac.post(
            "/execute",
            json={
                "code": "print('hello world')",
                "runner": "host",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["run"]["stdout"].strip() == "hello world"
    assert data["run"]["code"] == 0


@pytest.mark.asyncio
async def test_execute_with_stdin_host(client):
    """Code that reads stdin works on host runner."""
    async with client as ac:
        resp = await ac.post(
            "/execute",
            json={
                "code": "name = input()\nprint(f'hi {name}')",
                "stdin": "Alice",
                "runner": "host",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["run"]["stdout"].strip() == "hi Alice"


@pytest.mark.asyncio
async def test_execute_syntax_error(client):
    """Syntax errors are caught by AST validation."""
    async with client as ac:
        resp = await ac.post(
            "/execute",
            json={
                "code": "def foo(\n",
                "runner": "host",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["run"]["code"] == -1
    assert "Syntax Error" in data["run"]["stderr"]


@pytest.mark.asyncio
async def test_security_blocked_import(client):
    """Blocked imports are rejected."""
    async with client as ac:
        resp = await ac.post(
            "/execute",
            json={
                "code": "import os\nos.system('ls')",
                "runner": "host",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["run"]["code"] == -1
    assert "Security Error" in data["run"]["stderr"]


@pytest.mark.asyncio
async def test_security_blocked_subprocess(client):
    """Subprocess import is blocked."""
    async with client as ac:
        resp = await ac.post(
            "/execute",
            json={
                "code": "import subprocess\nsubprocess.run(['ls'])",
                "runner": "host",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "blocked" in data["run"]["stderr"].lower()


@pytest.mark.asyncio
async def test_security_blocked_eval(client):
    """eval() calls are blocked."""
    async with client as ac:
        resp = await ac.post(
            "/execute",
            json={
                "code": "eval('1+1')",
                "runner": "host",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "blocked" in data["run"]["stderr"].lower()


@pytest.mark.asyncio
async def test_security_blocked_dunder(client):
    """Access to __subclasses__ is blocked."""
    async with client as ac:
        resp = await ac.post(
            "/execute",
            json={
                "code": "x = ''.__class__.__subclasses__()",
                "runner": "host",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "blocked" in data["run"]["stderr"].lower()


@pytest.mark.asyncio
async def test_unsupported_language(client):
    """Non-Python languages return 400."""
    async with client as ac:
        resp = await ac.post(
            "/execute",
            json={
                "code": "console.log('hi')",
                "language": "javascript",
            },
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_execute_runtime_error_host(client):
    """Runtime errors are captured properly."""
    async with client as ac:
        resp = await ac.post(
            "/execute",
            json={
                "code": "x = 1 / 0",
                "runner": "host",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["run"]["code"] != 0
    assert "ZeroDivisionError" in data["run"]["stderr"]


# --- Docker Runner Tests (require Docker to be running) ---


@pytest.mark.asyncio
@pytest.mark.docker
async def test_execute_docker_simple(client):
    """Simple execution in Docker container."""
    async with client as ac:
        resp = await ac.post(
            "/execute",
            json={
                "code": "print(2 + 2)",
                "runner": "docker",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["run"]["stdout"].strip() == "4"
    assert data["run"]["code"] == 0


@pytest.mark.asyncio
@pytest.mark.docker
async def test_execute_docker_with_stdin(client):
    """Docker execution with stdin."""
    async with client as ac:
        resp = await ac.post(
            "/execute",
            json={
                "code": "n = int(input())\nprint(n * 3)",
                "stdin": "7",
                "runner": "docker",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["run"]["stdout"].strip() == "21"


@pytest.mark.asyncio
@pytest.mark.docker
async def test_batch_test_cases(client):
    """Batch test cases run in a single container."""
    async with client as ac:
        resp = await ac.post(
            "/execute",
            json={
                "code": "n = int(input())\nprint(n ** 2)",
                "test_cases": [
                    {"input": "2", "expected_output": "4"},
                    {"input": "3", "expected_output": "9"},
                    {"input": "5", "expected_output": "25"},
                    {"input": "0", "expected_output": "0"},
                ],
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total"] == 4
    assert data["summary"]["passed"] == 4
    assert data["summary"]["failed"] == 0
    for r in data["results"]:
        assert r["passed"] is True


@pytest.mark.asyncio
@pytest.mark.docker
async def test_batch_with_failure(client):
    """Batch correctly identifies failing test cases."""
    async with client as ac:
        resp = await ac.post(
            "/execute",
            json={
                "code": "n = int(input())\nprint(n + 1)",
                "test_cases": [
                    {"input": "1", "expected_output": "2"},
                    {"input": "2", "expected_output": "5"},  # Wrong: 3 != 5
                ],
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["passed"] == 1
    assert data["summary"]["failed"] == 1
    assert data["results"][0]["passed"] is True
    assert data["results"][1]["passed"] is False


@pytest.mark.asyncio
@pytest.mark.docker
async def test_batch_no_expected_output(client):
    """Batch without expected_output just runs code (passed=None)."""
    async with client as ac:
        resp = await ac.post(
            "/execute",
            json={
                "code": "print(input().upper())",
                "test_cases": [
                    {"input": "hello"},
                    {"input": "world"},
                ],
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"][0]["stdout"].strip() == "HELLO"
    assert data["results"][1]["stdout"].strip() == "WORLD"
    assert data["results"][0]["passed"] is None
