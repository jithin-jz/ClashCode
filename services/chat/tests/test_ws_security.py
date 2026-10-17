import json
import os

import pytest
from starlette.websockets import WebSocketDisconnect

os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_PUBLIC_KEY", "dummy_key")

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from main import app

from core import auth
from core.managers import NotificationManager

client = TestClient(app)
VALID = {"user_id": 7, "username": "u", "jti": "abc"}


def _connect_expecting_close(path: str, **kwargs):
    with pytest.raises(WebSocketDisconnect) as exc, client.websocket_connect(path, **kwargs):
        pass
    return exc.value.code


@patch("api.websockets.is_revoked", new_callable=AsyncMock, return_value=False)
@patch("api.websockets.verify_jwt", return_value=VALID)
def test_foreign_origin_is_rejected(_verify, _revoked):
    code = _connect_expecting_close(
        "/ws/notifications", headers={"authorization": "Bearer x", "origin": "https://evil.example"}
    )
    assert code == 1008


@patch("api.websockets.verify_jwt", return_value=None)
def test_query_string_token_is_not_accepted(mock_verify):
    _connect_expecting_close("/ws/notifications?token=some.jwt.value")
    mock_verify.assert_called_with("")


@patch("api.websockets.is_revoked", new_callable=AsyncMock, return_value=True)
@patch("api.websockets.verify_jwt", return_value=VALID)
def test_revoked_token_is_rejected(_verify, _revoked):
    assert _connect_expecting_close("/ws/tasks", headers={"authorization": "Bearer x"}) == 1008


def test_allowed_origin_check():
    ws = MagicMock()
    ws.headers = {"origin": auth.ALLOWED_ORIGINS[0]}
    assert auth.is_origin_allowed(ws)
    ws.headers = {}
    assert auth.is_origin_allowed(ws)  # non-browser client
    ws.headers = {"origin": "https://evil.example"}
    assert not auth.is_origin_allowed(ws)


@pytest.mark.asyncio
async def test_is_revoked_checks_jti_and_disabled_user():
    with patch.object(auth, "redis_client") as redis:
        redis.exists = AsyncMock(return_value=1)
        assert await auth.is_revoked(VALID) is True
        keys = redis.exists.call_args.args
        assert "auth:disabled_user:7" in keys
        assert "auth:revoked_jti:abc" in keys

        redis.exists = AsyncMock(side_effect=ConnectionError("down"))
        assert await auth.is_revoked(VALID) is False


@pytest.mark.asyncio
async def test_notification_manager_uses_one_pattern_subscription():
    manager = NotificationManager()
    ws_a, ws_b = AsyncMock(), AsyncMock()
    manager.active = {1: [ws_a], 2: [ws_b]}

    events = [
        {"type": "psubscribe", "channel": "notifications_*", "data": 1},
        {"type": "pmessage", "channel": "notifications_1", "data": json.dumps({"type": "task_completed"})},
        {"type": "pmessage", "channel": "notifications_99", "data": json.dumps({"type": "ignored"})},
    ]

    async def listen():
        for event in events:
            yield event

    pubsub = MagicMock()
    pubsub.psubscribe = AsyncMock()
    pubsub.punsubscribe = AsyncMock()
    pubsub.aclose = AsyncMock()
    pubsub.listen = listen

    with patch("core.managers.redis_client") as redis:
        redis.pubsub = MagicMock(return_value=pubsub)
        await manager.notification_subscriber()

    pubsub.psubscribe.assert_called_once_with("notifications_*")
    ws_a.send_text.assert_called_once()
    ws_b.send_text.assert_not_called()
