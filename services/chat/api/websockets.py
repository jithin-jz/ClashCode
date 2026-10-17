import contextlib
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from schemas import IncomingMessage

from core.auth import get_token, is_origin_allowed, is_revoked, verify_jwt
from core.managers import notification_manager
from services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter()


async def _authenticate(ws: WebSocket) -> dict | None:
    """Origin allowlist, token signature/expiry, then core's revocation list. Closes on failure."""
    if not is_origin_allowed(ws):
        logger.warning(f"Rejected WebSocket from disallowed origin: {ws.headers.get('origin')}")
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    payload = verify_jwt(get_token(ws) or "")
    if not payload or await is_revoked(payload):
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    return payload


@router.websocket("/ws/chat/{room}")
@router.websocket("/ws/chat/{room}/")
async def chat_ws(ws: WebSocket, room: str):
    # Room names: "global" or short alphanumeric identifiers
    if not room or len(room) > 50 or not (room == "global" or room.isalnum()):
        logger.warning(f"Invalid room access attempt: {room}")
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    payload = await _authenticate(ws)
    if not payload:
        return

    # Handle connection and join presence
    if not await ChatService.handle_connect(ws, room, payload):
        return

    try:
        while True:
            raw = await ws.receive_text()
            try:
                incoming = IncomingMessage.model_validate_json(raw)
            except Exception as parse_err:
                logger.warning(f"Invalid WS message from user {payload.get('user_id')}: {parse_err}")
                await ws.send_json({"type": "error", "message": "Invalid message format"})
                continue

            try:
                result = await ChatService.process_message(room, payload, incoming)
                if result:
                    if result.get("error"):
                        await ws.send_json({"type": "error", "message": result["error"]})
                    elif result.get("ok") is False:
                        reason = result.get("reason", "unknown")
                        logger.warning(f"Action '{incoming.action}' failed for user {payload.get('user_id')}: {reason}")
                        await ws.send_json(
                            {
                                "type": "error",
                                "message": f"Action failed: {reason}",
                                "action": incoming.action,
                            }
                        )
            except Exception as proc_err:
                logger.exception(f"Error processing '{incoming.action}' from user {payload.get('user_id')}: {proc_err}")
                with contextlib.suppress(Exception):
                    await ws.send_json({"type": "error", "message": "Server error processing action"})

    except WebSocketDisconnect:
        await ChatService.handle_disconnect(ws, room, payload)
    except Exception as e:
        logger.error(f"Chat WS fatal error: {e}")
        await ChatService.handle_disconnect(ws, room, payload)


async def _user_push_ws(ws: WebSocket, label: str):
    payload = await _authenticate(ws)
    if not payload:
        return

    user_id = int(payload["user_id"])
    await notification_manager.connect(ws, user_id)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await notification_manager.disconnect(ws, user_id)
    except Exception as e:
        logger.error(f"{label} WS error: {e}")
        await notification_manager.disconnect(ws, user_id)


@router.websocket("/ws/tasks")
@router.websocket("/ws/tasks/")
async def tasks_ws(ws: WebSocket):
    await _user_push_ws(ws, "Task Hub")


@router.websocket("/ws/notifications")
@router.websocket("/ws/notifications/")
async def notifications_ws(ws: WebSocket):
    await _user_push_ws(ws, "Notifications")
