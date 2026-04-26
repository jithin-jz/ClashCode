import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unauthorized_hints():
    response = client.post(
        "/hints",
        json={"user_code": "print(1)", "challenge_slug": "test", "hint_level": 1},
    )
    assert response.status_code == 403


def test_unauthorized_analyze():
    response = client.post(
        "/analyze", json={"user_code": "print(1)", "challenge_slug": "test"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
@patch("api.routes.fetch_challenge_context")
@patch("core.ai_logic.get_rag_context")
@patch("core.ai_logic.LLMFactory")
async def test_generate_hint_success(mock_factory, mock_rag, mock_fetch):
    mock_fetch.return_value = {"title": "Test", "description": "Test"}
    mock_rag.return_value = "RAG"

    # Use RunnableLambda to satisfy LangChain's pipe requirements
    mock_llm = RunnableLambda(lambda x: AIMessage(content="Try using a loop."))

    mock_factory.get_llm.return_value = mock_llm
    mock_factory.get_fallback_llm.return_value = mock_llm

    headers = {"X-Internal-API-Key": "test-secret"}
    payload = {"user_code": "print(1)", "challenge_slug": "test", "hint_level": 1}

    response = client.post("/hints", json=payload, headers=headers)

    assert response.status_code == 200
    assert response.json()["hint"] == "Try using a loop."


@pytest.mark.asyncio
@patch("api.routes.fetch_challenge_context")
@patch("core.ai_logic.get_rag_context")
@patch("core.ai_logic.LLMFactory")
async def test_analyze_code_success(mock_factory, mock_rag, mock_fetch):
    mock_fetch.return_value = {
        "title": "T",
        "description": "D",
        "initial_code": "",
        "test_code": "",
    }
    mock_rag.return_value = "R"

    mock_llm = RunnableLambda(lambda x: AIMessage(content="Findings: Good."))

    mock_factory.get_llm.return_value = mock_llm
    mock_factory.get_fallback_llm.return_value = mock_llm

    headers = {"X-Internal-API-Key": "test-secret"}
    payload = {"user_code": "print(1)", "challenge_slug": "test"}

    response = client.post("/analyze", json=payload, headers=headers)

    assert response.status_code == 200
    assert "Findings" in response.json()["review"]
