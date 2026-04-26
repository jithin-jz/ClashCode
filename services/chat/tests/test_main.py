import os

import pytest

# Set dummy environment variables BEFORE importing main app
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["JWT_PUBLIC_KEY"] = "dummy_key"

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "chat"}


def test_history_no_token():
    response = client.get("/history/general")
    assert response.status_code == 401
    assert response.json()["error"] == "Invalid token"


@patch("api.routes.verify_jwt")
def test_history_invalid_token(mock_verify):
    mock_verify.return_value = None
    response = client.get("/history/general", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
    assert response.json()["error"] == "Invalid token"


@pytest.mark.asyncio
@patch("api.routes.verify_jwt")
@patch("services.chat_service.dynamo_client")
async def test_history_success_dynamo(mock_dynamo, mock_verify):
    # Setup mocks
    mock_verify.return_value = {"user_id": 1, "username": "testuser"}
    mock_dynamo.get_messages = AsyncMock(
        return_value={
            "items": [
                {
                    "sender": "user1",
                    "content": "hello",
                    "timestamp": "2023-01-01T00:00:00",
                    "reactions": {},
                }
            ],
            "last_evaluated_key": None,
        }
    )

    # We use TestClient which is synchronous, but the endpoint is async.
    # TestClient handles async endpoints internally by running them in an event loop.
    response = client.get("/history/general", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "dynamodb"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["message"] == "hello"


@pytest.mark.asyncio
@patch("api.routes.verify_jwt")
@patch("services.chat_service.dynamo_client")
async def test_history_empty_dynamo(mock_dynamo, mock_verify):
    mock_verify.return_value = {"user_id": 1, "username": "testuser"}
    mock_dynamo.get_messages = AsyncMock(return_value={"items": [], "last_evaluated_key": None})

    response = client.get("/history/general", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "dynamodb"
    assert data["messages"] == []
