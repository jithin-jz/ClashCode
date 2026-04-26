import json
import os

import pytest
from starlette.websockets import WebSocketDisconnect

# Set dummy environment variables BEFORE importing main app
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["JWT_PUBLIC_KEY"] = "dummy_key"

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.mark.asyncio
@patch("api.websockets.verify_jwt")
@patch("services.chat_service.rate_limiter")
async def test_websocket_auth_failure(mock_limiter, mock_verify):
    mock_verify.return_value = None

    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            "/ws/chat/global",
            headers={"authorization": "Bearer invalid"},
        ) as _:
            pass
    assert exc.value.code == 1008


@pytest.mark.asyncio
@patch("api.websockets.verify_jwt")
@patch("services.chat_service.rate_limiter")
@patch("services.chat_service.redis_client")
@patch("services.chat_service.dynamo_client")
async def test_websocket_success_flow(mock_dynamo, mock_redis, mock_limiter, mock_verify):
    # Setup Auth
    mock_verify.return_value = {"user_id": 1, "username": "testuser"}

    # Setup Rate Limiter
    mock_limiter.check_connection_rate = AsyncMock(return_value=True)
    mock_limiter.check_message_rate = AsyncMock(return_value=True)
    mock_limiter.check_burst_rate = AsyncMock(return_value=True)

    # Mock Redis (Sync container)
    mock_redis.publish = AsyncMock()

    # Mock pubsub for subscriber task
    # Note: .pubsub() is a sync call in redis-py
    mock_pubsub = MagicMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()

    # Mock listen to be an async generator
    async def empty_gen():
        if False:
            yield None

    mock_pubsub.listen.return_value = empty_gen()

    # Force .pubsub() to return our mock_pubsub directly (not a coroutine)
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

    # Mock Dynamo
    mock_dynamo.get_messages = AsyncMock(return_value={"items": [], "last_evaluated_key": None})
    mock_dynamo.save_message = AsyncMock()

    with client.websocket_connect(
        "/ws/chat/global",
        headers={"authorization": "Bearer valid"},
    ) as websocket:
        # Send a message
        websocket.send_text(json.dumps({"message": "hello world"}))

    # Verify side effects
    # 1. Dynamo Save
    mock_dynamo.save_message.assert_called()
    # 2. Redis Publish (Presence + Message)
    assert mock_redis.publish.call_count >= 2


@pytest.mark.asyncio
@patch("api.websockets.verify_jwt")
@patch("services.chat_service.rate_limiter")
@patch("services.chat_service.redis_client")
@patch("services.chat_service.dynamo_client")
async def test_websocket_delete_forbidden_stays_local(mock_dynamo, mock_redis, mock_limiter, mock_verify):
    mock_verify.return_value = {"user_id": 1, "username": "testuser"}
    mock_limiter.check_connection_rate = AsyncMock(return_value=True)
    mock_limiter.check_message_rate = AsyncMock(return_value=True)
    mock_limiter.check_burst_rate = AsyncMock(return_value=True)
    mock_dynamo.get_messages = AsyncMock(return_value={"items": [], "last_evaluated_key": None})
    mock_dynamo.delete_message = AsyncMock(return_value={"ok": False, "error": "You can only delete your own messages"})
    mock_redis.publish = AsyncMock()

    mock_pubsub = MagicMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()

    async def empty_gen():
        if False:
            yield None

    mock_pubsub.listen.return_value = empty_gen()
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

    with client.websocket_connect(
        "/ws/chat/global",
        headers={"authorization": "Bearer valid"},
    ) as websocket:
        websocket.send_text(
            json.dumps(
                {
                    "action": "delete",
                    "target_timestamp": "2023-01-01T00:00:00",
                }
            )
        )
        response = websocket.receive_json()

    assert response["type"] == "error"
    assert "delete your own messages" in response["message"]
