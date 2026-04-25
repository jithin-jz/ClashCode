from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status, Request
from fastapi.responses import JSONResponse
import os, json, jwt, asyncio, logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from decimal import Decimal
import redis.asyncio as redis
from dotenv import load_dotenv
from typing import Dict, List, Any

import re
from schemas import ChatMessage as ChatMessageSchema, PresenceEvent, IncomingMessage
from rate_limiter import RateLimiter
from dynamo import dynamo_client

# Configure structured logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# JSON Encoder for Boto3/DynamoDB Decimals
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o % 1 == 0 else float(o)
        return super().default(o)


def json_dumps(obj: Any) -> str:
    return json.dumps(obj, cls=DecimalEncoder)


load_dotenv()

# Sentry initialization
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        environment=os.getenv("ENVIRONMENT", "development"),
        integrations=[FastApiIntegration()],
    )
    logger.info("Sentry initialized for Chat service")

# --------------------------------------------------
# Config
# --------------------------------------------------

app = FastAPI(title="Chat Service")

# JWT Configuration (RS256 - asymmetric)
ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256").upper()
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "").replace("\\n", "\n").strip()
JWT_SHARED_SECRET = (
    os.getenv("JWT_SHARED_SECRET", "").strip() or os.getenv("SECRET_KEY", "").strip()
)
JWT_VERIFY_KEY = JWT_PUBLIC_KEY
if not JWT_VERIFY_KEY and JWT_SHARED_SECRET:
    ALGORITHM = "HS256"
    JWT_VERIFY_KEY = JWT_SHARED_SECRET
JWT_ACCESS_COOKIE_NAME = os.getenv("JWT_ACCESS_COOKIE_NAME", "access_token")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)
rate_limiter = RateLimiter(redis_client)

# Chat config
HISTORY_LIMIT = 50
TYPING_INDICATOR_TTL = 3  # seconds


@app.on_event("startup")
async def on_startup():
    await dynamo_client.create_table_if_not_exists()


@app.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    return JSONResponse(
        content={"status": "ok", "service": "chat"}, status_code=status.HTTP_200_OK
    )


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        content={"error": "Internal server error"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@app.get("/history/{room}")
async def get_message_history(
    request: Request,
    room: str,
    limit: int = 50,
    offset: int = 0,
):
    """Get paginated message history for a room."""
    token = get_token(request)
    payload = verify_jwt(token or "")
    if not payload:
        return JSONResponse(
            content={"error": "Invalid token"}, status_code=status.HTTP_401_UNAUTHORIZED
        )

    try:
        fetch_limit = limit + max(offset, 0)
        messages = await dynamo_client.get_messages(room, limit=fetch_limit)
        paged_messages = messages[offset : offset + limit]

        return JSONResponse(
            content={
                "messages": [
                    serialize_dynamo_message(room, msg)
                    for msg in reversed(paged_messages)
                ],
                "has_more": len(messages) > offset + len(paged_messages),
                "source": "dynamodb",
            },
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        logger.error(f"Error fetching message history: {e}", exc_info=True)
        return JSONResponse(
            content={"error": "Failed to fetch message history"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def serialize_dynamo_message(room: str, item: dict) -> dict:
    """Safely serialize a DynamoDB item for the frontend."""
    return {
        "room": room,
        "message": item.get("content", ""),
        "user_id": item.get("user_id"),
        "username": item.get("sender") or item.get("username") or "Unknown",
        "avatar_url": item.get("avatar_url"),
        "timestamp": item.get("timestamp"),
        "reactions": item.get("reactions", {}),
    }


# --------------------------------------------------
# Helpers
# --------------------------------------------------


def get_token(request: Request | WebSocket) -> str | None:
    token = None
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1]
    if not token:
        token = request.cookies.get(JWT_ACCESS_COOKIE_NAME)
    return token


def verify_jwt(token: str) -> dict | None:
    if not token:
        return None
    if not JWT_VERIFY_KEY:
        logger.warning("JWT verification key is not configured for the chat service.")
        return None
    try:
        payload = jwt.decode(
            token,
            JWT_VERIFY_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp"]},
        )
        if payload.get("type") != "access" or "user_id" not in payload:
            return None
        return payload
    except jwt.PyJWTError:
        return None


def channel_key(room: str) -> str:
    return f"chat:room:{room}"


# --------------------------------------------------
# Connection Managers
# --------------------------------------------------


class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, List[WebSocket]] = {}
        self.tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, ws: WebSocket, room: str):
        await ws.accept()
        self.active.setdefault(room, []).append(ws)

        # Start subscriber if first connection
        if len(self.active[room]) == 1 and room not in self.tasks:
            self.tasks[room] = asyncio.create_task(self.redis_subscriber(room))

    async def disconnect(self, ws: WebSocket, room: str):
        if room in self.active and ws in self.active[room]:
            self.active[room].remove(ws)

            # Cleanup if room empty
            if not self.active[room]:
                self.active.pop(room, None)
                if room in self.tasks:
                    self.tasks[room].cancel()
                    try:
                        await self.tasks[room]
                    except asyncio.CancelledError:
                        pass
                    self.tasks.pop(room, None)

    async def redis_subscriber(self, room: str):
        """Subscribes to Redis channel and broadcasts to local websockets."""
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel_key(room))

        try:
            async for event in pubsub.listen():
                if event["type"] == "message":
                    payload = json.loads(event["data"])
                    await self.broadcast_local(room, payload)
        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel_key(room))
            raise

    async def broadcast_local(self, room: str, payload: dict):
        dead = []
        message = json_dumps(payload)

        for ws in self.active.get(room, []):
            try:
                await ws.send_text(message)
            except ConnectionResetError:
                logger.warning(f"Connection reset while broadcasting to room {room}")
                dead.append(ws)
            except RuntimeError as e:
                logger.error(f"Runtime error broadcasting to room {room}: {e}")
                dead.append(ws)
            except Exception as e:
                logger.error(
                    f"Unexpected error broadcasting to room {room}: {e}", exc_info=True
                )
                dead.append(ws)

        for ws in dead:
            await self.disconnect(ws, room)


manager = ConnectionManager()


class NotificationManager:
    def __init__(self):
        self.active: Dict[int, List[WebSocket]] = {}
        self.tasks: Dict[int, asyncio.Task] = {}

    async def connect(self, ws: WebSocket, user_id: int):
        await ws.accept()
        self.active.setdefault(user_id, []).append(ws)

        if len(self.active[user_id]) == 1 and user_id not in self.tasks:
            self.tasks[user_id] = asyncio.create_task(
                self.notification_subscriber(user_id)
            )
            logger.info(f"Started notification subscriber for user {user_id}")

    async def disconnect(self, ws: WebSocket, user_id: int):
        if user_id in self.active and ws in self.active[user_id]:
            self.active[user_id].remove(ws)
            if not self.active[user_id]:
                self.active.pop(user_id, None)
                if user_id in self.tasks:
                    self.tasks[user_id].cancel()
                    try:
                        await self.tasks[user_id]
                    except asyncio.CancelledError:
                        pass
                    self.tasks.pop(user_id, None)
                    logger.info(f"Stopped notification subscriber for user {user_id}")

    async def notification_subscriber(self, user_id: int):
        pubsub = redis_client.pubsub()
        channel = f"notifications_{user_id}"
        await pubsub.subscribe(channel)

        try:
            async for event in pubsub.listen():
                if event["type"] == "message":
                    payload = json.loads(event["data"])
                    await self.broadcast_user(user_id, payload)
        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel)
            raise
        except Exception as e:
            logger.error(f"Error in notification subscriber for user {user_id}: {e}")
            await pubsub.unsubscribe(channel)

    async def broadcast_user(self, user_id: int, payload: dict):
        dead = []
        message = json_dumps(payload)
        for ws in self.active.get(user_id, []):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws, user_id)


notification_manager = NotificationManager()

# --------------------------------------------------
# WebSocket Endpoints
# --------------------------------------------------


@app.websocket("/ws/chat/{room}")
async def chat_ws(ws: WebSocket, room: str):
    # ---- room validation ----
    if room != "global":
        logger.warning(f"Unauthorized room access attempt: {room}")
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # ---- Auth ----
    token = get_token(ws)
    if not token:
        logger.warning(f"WebSocket connection rejected: no token (room={room})")
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    payload = verify_jwt(token)
    if not payload:
        logger.warning(f"WebSocket connection rejected: invalid JWT (room={room})")
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = payload["user_id"]
    username = payload.get("username", f"user-{user_id}")
    avatar_url = payload.get("avatar_url")

    # ---- Rate Limit: Connection ----
    if not await rate_limiter.check_connection_rate(user_id):
        logger.warning(f"WebSocket rate limited: user_id={user_id}")
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # ---- Connect ----
    await manager.connect(ws, room)

    # ---- Send history from DynamoDB ----
    history_data = []
    try:
        messages = await dynamo_client.get_messages(room, limit=HISTORY_LIMIT)
        if messages:
            history_data = [
                serialize_dynamo_message(room, message)
                for message in reversed(messages)
            ]
    except Exception as e:
        logger.error("Failed to load chat history from Dynamo for room %s: %s", room, e)

    if history_data:
        await ws.send_text(
            json_dumps(
                {
                    "type": "history",
                    "messages": history_data,
                }
            )
        )

    # ---- Send pinned message if exists ----
    try:
        pin_key = f"chat:pinned:{room}"
        pinned = await redis_client.get(pin_key)
        if pinned:
            pin_data = json.loads(pinned)
            await ws.send_text(
                json_dumps(
                    {
                        "type": "chat_pin",
                        **pin_data,
                        "room": room,
                    }
                )
            )
    except Exception:
        pass

    # ---- Presence join ----
    join = PresenceEvent(
        event="join",
        user_id=user_id,
        username=username,
        avatar_url=avatar_url,
        count=len(manager.active.get(room, [])),
    )
    await redis_client.publish(channel_key(room), join.model_dump_json())

    # ---- Message loop ----
    try:
        while True:
            raw = await ws.receive_text()

            incoming = IncomingMessage.model_validate_json(raw)

            # ---- Rate Limit: Message ----
            if not await rate_limiter.check_message_rate(user_id):
                # Send rate limit warning to user
                await ws.send_json(
                    {"type": "error", "message": "Rate limited: too many messages"}
                )
                continue

            if not await rate_limiter.check_burst_rate(user_id):
                # Send burst limit warning
                await ws.send_json(
                    {
                        "type": "error",
                        "message": "Slow down! Too many messages too fast",
                    }
                )
                continue

            if incoming.action == "delete" and incoming.target_timestamp:
                try:
                    result = await dynamo_client.delete_message(
                        room_id=room,
                        timestamp=incoming.target_timestamp,
                        user_id=user_id,
                    )
                except Exception as e:
                    logger.error(f"Failed to delete message in DynamoDB: {e}")
                    result = {"ok": False, "reason": "error"}

                if not result.get("ok"):
                    reason = result.get("reason")
                    await ws.send_json(
                        {
                            "type": "error",
                            "message": (
                                "Message not found."
                                if reason == "not_found"
                                else (
                                    "You can only delete your own messages."
                                    if reason == "forbidden"
                                    else "Could not delete message. Please try again."
                                )
                            ),
                        }
                    )
                    continue

                await redis_client.publish(
                    channel_key(room),
                    json_dumps(
                        {
                            "type": "chat_delete",
                            "timestamp": incoming.target_timestamp,
                            "user_id": user_id,
                            "room": room,
                        }
                    ),
                )
                continue

            if (
                incoming.action == "edit"
                and incoming.target_timestamp
                and incoming.message
            ):
                try:
                    result = await dynamo_client.edit_message(
                        room_id=room,
                        timestamp=incoming.target_timestamp,
                        user_id=user_id,
                        new_message=incoming.message,
                    )
                except Exception as e:
                    logger.error(f"Failed to edit message in DynamoDB: {e}")
                    result = {"ok": False, "reason": "error"}

                if not result.get("ok"):
                    reason = result.get("reason")
                    await ws.send_json(
                        {
                            "type": "error",
                            "message": (
                                "Message not found."
                                if reason == "not_found"
                                else (
                                    "You can only edit your own messages."
                                    if reason == "forbidden"
                                    else "Could not edit message. Please try again."
                                )
                            ),
                        }
                    )
                    continue

                await redis_client.publish(
                    channel_key(room),
                    json_dumps(
                        {
                            "type": "chat_edit",
                            "timestamp": incoming.target_timestamp,
                            "message": incoming.message,
                            "user_id": user_id,
                            "room": room,
                        }
                    ),
                )
                continue

            # ---- Typing Indicator ----
            if incoming.action == "typing":
                await redis_client.publish(
                    channel_key(room),
                    json_dumps(
                        {
                            "type": "typing",
                            "user_id": user_id,
                            "username": username,
                        }
                    ),
                )
                continue

            if (
                incoming.action == "react"
                and incoming.target_timestamp
                and incoming.emoji
            ):
                try:
                    result = await dynamo_client.toggle_reaction(
                        room_id=room,
                        timestamp=incoming.target_timestamp,
                        username=username,
                        emoji=incoming.emoji,
                    )
                except Exception as e:
                    logger.error(f"Failed to toggle reaction in DynamoDB: {e}")
                    result = {"ok": False, "reason": "error", "reactions": {}}

                if not result.get("ok"):
                    await ws.send_json(
                        {
                            "type": "error",
                            "message": "Message not found.",
                        }
                    )
                    continue

                await redis_client.publish(
                    channel_key(room),
                    json_dumps(
                        {
                            "type": "chat_react",
                            "timestamp": incoming.target_timestamp,
                            "emoji": incoming.emoji,
                            "username": username,
                            "user_id": user_id,
                            "reactions": result.get("reactions", {}),
                            "room": room,
                        }
                    ),
                )
                continue

            # ---- Pin / Unpin Message ----
            if incoming.action in ("pin", "unpin") and incoming.target_timestamp:
                pin_key = f"chat:pinned:{room}"
                if incoming.action == "pin":
                    await redis_client.set(
                        pin_key,
                        json_dumps(
                            {
                                "timestamp": incoming.target_timestamp,
                                "pinned_by": username,
                                "message": incoming.message or "",
                            }
                        ),
                    )
                else:
                    await redis_client.delete(pin_key)

                await redis_client.publish(
                    channel_key(room),
                    json_dumps(
                        {
                            "type": (
                                "chat_pin" if incoming.action == "pin" else "chat_unpin"
                            ),
                            "timestamp": incoming.target_timestamp,
                            "pinned_by": username,
                            "message": incoming.message or "",
                            "room": room,
                        }
                    ),
                )
                continue

            message = ChatMessageSchema(
                room=room,
                message=incoming.message,
                user_id=user_id,
                username=username,
                avatar_url=avatar_url,
            )

            # Detect @mentions for global notifications
            mentions = re.findall(r"@(\w+)", message.message)
            if mentions:
                for mention in set(mentions):
                    # Publish mention event.
                    await redis_client.publish(
                        "global_mentions",
                        json_dumps(
                            {
                                "type": "mention",
                                "target_username": mention,
                                "sender": username,
                                "room": room,
                                "message": message.message[:100],
                            }
                        ),
                    )

            try:
                await dynamo_client.save_message(
                    room_id=room,
                    sender=username,
                    message=incoming.message,
                    user_id=user_id,
                    avatar_url=avatar_url,
                    timestamp=message.timestamp,
                )
            except Exception as e:
                logger.error(f"Failed to save message to DynamoDB: {e}")
                await ws.send_json(
                    {
                        "type": "error",
                        "message": "Message could not be saved. Please try again.",
                    }
                )
                continue

            # Publish
            await redis_client.publish(
                channel_key(room),
                message.model_dump_json(),
            )

    except WebSocketDisconnect:
        await manager.disconnect(ws, room)

        leave = PresenceEvent(
            event="leave",
            user_id=user_id,
            username=username,
            avatar_url=avatar_url,
            count=len(manager.active.get(room, [])),
        )
        await redis_client.publish(channel_key(room), leave.model_dump_json())

    except Exception as e:
        logger.error(f"Error in chat websocket: {e}")
        await manager.disconnect(ws, room)


@app.websocket("/ws/tasks/")
async def tasks_ws(ws: WebSocket):
    """
    Dedicated websocket for real-time task notifications.
    Standardized to handle AI hints and analysis status updates.
    """
    # Authenticate
    token = ws.query_params.get("token") or ws.cookies.get(JWT_ACCESS_COOKIE_NAME)
    if not token:
        # Check Authorization header (though browser WebSockets don't easily support this)
        auth = ws.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]

    payload = verify_jwt(token or "")
    if not payload:
        logger.warning("Unauthenticated task WS attempt")
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = int(payload.get("user_id"))
    logger.info(f"Task Hub connected for user {user_id}")

    await notification_manager.connect(ws, user_id)
    try:
        while True:
            # We don't expect messages from client here, just keep connection alive
            await ws.receive_text()
    except WebSocketDisconnect:
        await notification_manager.disconnect(ws, user_id)
    except Exception as e:
        logger.error(f"Error in task hub websocket: {e}")
        await notification_manager.disconnect(ws, user_id)


@app.websocket("/ws/notifications/")
async def notifications_ws(ws: WebSocket):
    # ---- Auth ----
    token = get_token(ws)
    if not token:
        logger.warning("Notification WebSocket connection rejected: no token")
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    payload = verify_jwt(token)
    if not payload:
        logger.warning("Notification WebSocket connection rejected: invalid JWT")
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = payload["user_id"]

    # ---- Connect ----
    await notification_manager.connect(ws, user_id)

    # ---- Keep alive loop ----
    try:
        while True:
            # Just wait for messages or disconnection
            await ws.receive_text()
    except WebSocketDisconnect:
        await notification_manager.disconnect(ws, user_id)
    except Exception as e:
        logger.error(f"Error in notifications websocket: {e}")
        await notification_manager.disconnect(ws, user_id)
