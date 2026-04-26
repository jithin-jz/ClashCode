import logging

from core.auth import JWT_ACCESS_COOKIE_NAME, get_token, verify_jwt
from core.managers import notification_manager
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from schemas import IncomingMessage
from services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/chat/{room}")
@router.websocket("/ws/chat/{room}/")
async def chat_ws(ws: WebSocket, room: str):
    if room != "global":
        logger.warning(f"Unauthorized room access attempt: {room}")
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    token = get_token(ws)
    if not token:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    payload = verify_jwt(token)
    if not payload:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Handle connection and join presence
    if not await ChatService.handle_connect(ws, room, payload):
        return

    try:
        while True:
            raw = await ws.receive_text()
            incoming = IncomingMessage.model_validate_json(raw)

            result = await ChatService.process_message(room, payload, incoming)
            if result and "error" in result:
                await ws.send_json({"type": "error", "message": result["error"]})

    except WebSocketDisconnect:
        await ChatService.handle_disconnect(ws, room, payload)
    except Exception as e:
        logger.error(f"Chat WS error: {e}")
        await ChatService.handle_disconnect(ws, room, payload)


@router.websocket("/ws/tasks")
@router.websocket("/ws/tasks/")
async def tasks_ws(ws: WebSocket):
    token = ws.query_params.get("token") or ws.cookies.get(JWT_ACCESS_COOKIE_NAME)
    if not token:
        auth = ws.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]

    payload = verify_jwt(token or "")
    if not payload:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = int(payload.get("user_id"))
    await notification_manager.connect(ws, user_id)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await notification_manager.disconnect(ws, user_id)
    except Exception as e:
        logger.error(f"Task Hub WS error: {e}")
        await notification_manager.disconnect(ws, user_id)


@router.websocket("/ws/notifications")
@router.websocket("/ws/notifications/")
async def notifications_ws(ws: WebSocket):
    token = get_token(ws)
    payload = verify_jwt(token or "")
    if not payload:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = payload["user_id"]
    await notification_manager.connect(ws, user_id)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await notification_manager.disconnect(ws, user_id)
    except Exception as e:
        logger.error(f"Notifications WS error: {e}")
        await notification_manager.disconnect(ws, user_id)
