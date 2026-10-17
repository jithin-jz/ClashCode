from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core import agent_tools
from core.security import build_executor_headers
from utils import executor_client


def test_executor_headers_fall_back_to_internal_key():
    headers = build_executor_headers("/execute")
    assert headers["X-Internal-API-Key"] == "test-secret"


def test_executor_headers_prefer_dedicated_key():
    with patch.object(executor_client.settings, "EXECUTOR_API_KEY", "exec-key"):
        assert build_executor_headers("/execute")["X-Internal-API-Key"] == "exec-key"


@pytest.mark.asyncio
async def test_sandbox_client_sends_tests_separately_and_reads_passed():
    response = MagicMock(status_code=200)
    response.json.return_value = {"passed": False, "run": {"stdout": "", "stderr": "", "code": 0}}
    client = MagicMock()
    client.post = AsyncMock(return_value=response)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)

    with patch.object(executor_client.httpx, "AsyncClient", return_value=client):
        result = await executor_client.run_tests_in_sandbox("exit()", "assert f() == 1")

    payload = client.post.call_args.kwargs["json"]
    assert payload["code"] == "exit()"
    assert payload["test_code"] == "assert f() == 1"
    # Exit code 0 is not a pass without the harness flag.
    assert result["passed"] is False


@pytest.mark.asyncio
async def test_agent_tool_reports_failure_when_harness_did_not_pass():
    fake = AsyncMock(return_value={"ok": True, "passed": False, "stdout": "", "stderr": "", "exit_code": 0})
    with patch.object(agent_tools, "run_tests_in_sandbox", fake):
        tools = agent_tools.build_tools(
            challenge_slug="s", challenge_description="d", user_code="exit()", test_code="assert True"
        )
        run_tool = next(t for t in tools if t.name == "run_challenge_tests")
        output = await run_tool.ainvoke({})
    assert output.startswith("Tests FAILED")
