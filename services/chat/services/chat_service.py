import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from fastapi import WebSocket, status

from core.managers import manager
from core.serializers import json_dumps, serialize_dynamo_message
from utils.redis_client import redis_client, rate_limiter, channel_key
from dynamo import dynamo_client
from schemas import ChatMessage as ChatMessageSchema, PresenceEvent, IncomingMessage

logger = logging.getLogger(__name__)

class ChatService:
    @staticmethod
    async def handle_connect(ws: WebSocket, room: str, user_payload: Dict[str, Any]) -> bool:
        """Handles new WebSocket connection, sends history and joins presence."""
        user_id = user_payload["user_id"]
        username = user_payload.get("username", f"user-{user_id}")
        avatar_url = user_payload.get("avatar_url")

        if not await rate_limiter.check_connection_rate(user_id):
            await ws.close(code=status.WS_1008_POLICY_VIOLATION)
            return False

        await manager.connect(ws, room)

        # 1. Send History
        try:
            result = await dynamo_client.get_messages(room, limit=50)
            messages = result.get("items", [])
            if messages:
                history_data = [serialize_dynamo_message(room, msg) for msg in reversed(messages)]
                last_key = result.get("last_evaluated_key")
                await ws.send_text(json_dumps({
                    "type": "history", 
                    "messages": history_data,
                    "last_timestamp": last_key.get("timestamp") if last_key else None
                }))
        except Exception as e:
            logger.error(f"Failed to load history for room {room}: {e}")

        # 2. Send Pinned Message
        try:
            pinned = await redis_client.get(f"chat:pinned:{room}")
            if pinned:
                await ws.send_text(json_dumps({"type": "chat_pin", **json.loads(pinned), "room": room}))
        except Exception:
            pass

        # 3. Publish Presence Join
        join = PresenceEvent(
            event="join", user_id=user_id, username=username,
            avatar_url=avatar_url, count=len(manager.active.get(room, []))
        )
        await redis_client.publish(channel_key(room), join.model_dump_json())
        return True

    @staticmethod
    async def handle_disconnect(ws: WebSocket, room: str, user_payload: Dict[str, Any]):
        """Handles WebSocket disconnection and leaves presence."""
        user_id = user_payload["user_id"]
        username = user_payload.get("username", f"user-{user_id}")
        avatar_url = user_payload.get("avatar_url")

        await manager.disconnect(ws, room)
        
        leave = PresenceEvent(
            event="leave", user_id=user_id, username=username,
            avatar_url=avatar_url, count=len(manager.active.get(room, []))
        )
        await redis_client.publish(channel_key(room), leave.model_dump_json())

    @staticmethod
    async def process_message(room: str, user_payload: Dict[str, Any], incoming: IncomingMessage):
        """Processes incoming chat messages based on action type."""
        user_id = user_payload["user_id"]
        username = user_payload.get("username", f"user-{user_id}")
        avatar_url = user_payload.get("avatar_url")

        # Rate Limiting
        if not await rate_limiter.check_message_rate(user_id) or not await rate_limiter.check_burst_rate(user_id):
            return {"error": "Rate limited"}

        if incoming.action == "delete":
            return await ChatService._handle_delete(room, user_id, incoming)
        
        if incoming.action == "edit":
            return await ChatService._handle_edit(room, user_id, incoming)
        
        if incoming.action == "typing":
            return await ChatService._handle_typing(room, user_id, username)
        
        if incoming.action == "react":
            return await ChatService._handle_react(room, user_id, username, incoming)
        
        if incoming.action in ("pin", "unpin"):
            return await ChatService._handle_pin(room, username, incoming)

        if incoming.action == "read":
            return await ChatService._handle_read(room, username, user_id, incoming)

        # Default: Standard Message
        return await ChatService._handle_standard_message(room, user_id, username, avatar_url, incoming)

    @staticmethod
    async def _handle_delete(room: str, user_id: int, incoming: IncomingMessage):
        result = await dynamo_client.delete_message(room, incoming.target_timestamp, user_id)
        if result.get("ok"):
            await redis_client.publish(channel_key(room), json_dumps({
                "type": "chat_delete", "timestamp": incoming.target_timestamp,
                "user_id": user_id, "room": room
            }))
        return result

    @staticmethod
    async def _handle_edit(room: str, user_id: int, incoming: IncomingMessage):
        result = await dynamo_client.edit_message(room, incoming.target_timestamp, user_id, incoming.message)
        if result.get("ok"):
            await redis_client.publish(channel_key(room), json_dumps({
                "type": "chat_edit", "timestamp": incoming.target_timestamp,
                "message": incoming.message, "user_id": user_id, "room": room
            }))
        return result

    @staticmethod
    async def _handle_typing(room: str, user_id: int, username: str):
        await redis_client.publish(channel_key(room), json_dumps({
            "type": "typing", "user_id": user_id, "username": username
        }))
        return {"ok": True}

    @staticmethod
    async def _handle_react(room: str, user_id: int, username: str, incoming: IncomingMessage):
        result = await dynamo_client.toggle_reaction(room, incoming.target_timestamp, username, incoming.emoji)
        if result.get("ok"):
            await redis_client.publish(channel_key(room), json_dumps({
                "type": "chat_react", "timestamp": incoming.target_timestamp,
                "emoji": incoming.emoji, "username": username, "user_id": user_id,
                "reactions": result.get("reactions", {}), "room": room
            }))
        return result

    @staticmethod
    async def _handle_pin(room: str, username: str, incoming: IncomingMessage):
        pin_key = f"chat:pinned:{room}"
        if incoming.action == "pin":
            await redis_client.set(pin_key, json_dumps({
                "timestamp": incoming.target_timestamp, "pinned_by": username,
                "message": incoming.message or ""
            }))
        else:
            await redis_client.delete(pin_key)
        
        await redis_client.publish(channel_key(room), json_dumps({
            "type": "chat_pin" if incoming.action == "pin" else "chat_unpin",
            "timestamp": incoming.target_timestamp, "pinned_by": username,
            "message": incoming.message or "", "room": room
        }))
        return {"ok": True}

    @staticmethod
    async def _handle_read(room: str, username: str, user_id: int, incoming: IncomingMessage):
        if not incoming.target_timestamp:
            return {"error": "target_timestamp required"}
        
        result = await dynamo_client.mark_as_read(room, incoming.target_timestamp, username)
        if result.get("ok"):
            await redis_client.publish(channel_key(room), json_dumps({
                "type": "chat_read", "timestamp": incoming.target_timestamp,
                "username": username, "user_id": user_id, "room": room
            }))
        return result

    @staticmethod
    async def _handle_standard_message(room: str, user_id: int, username: str, avatar_url: str, incoming: IncomingMessage):
        message = ChatMessageSchema(
            room=room, message=incoming.message, user_id=user_id,
            username=username, avatar_url=avatar_url
        )

        # Handle Mentions
        mentions = re.findall(r"@(\w+)", message.message)
        for mention in set(mentions):
            await redis_client.publish("global_mentions", json_dumps({
                "type": "mention", "target_username": mention, "sender": username,
                "room": room, "message": message.message[:100]
            }))

        # Save to DynamoDB
        await dynamo_client.save_message(
            room_id=room, sender=username, message=incoming.message,
            user_id=user_id, avatar_url=avatar_url, timestamp=message.timestamp
        )
        
        # Broadcast via Redis
        await redis_client.publish(channel_key(room), message.model_dump_json())
        return {"ok": True}

    @staticmethod
    async def get_history(room: str, limit: int = 50, last_timestamp: str | None = None) -> Dict[str, Any]:
        """Retrieves paginated message history for a room using a cursor (last_timestamp)."""
        result = await dynamo_client.get_messages(room, limit=limit, last_timestamp=last_timestamp)
        messages = result.get("items", [])
        last_key = result.get("last_evaluated_key")

        return {
            "messages": [
                serialize_dynamo_message(room, msg)
                for msg in reversed(messages)
            ],
            "last_timestamp": last_key.get("timestamp") if last_key else None,
            "has_more": last_key is not None,
            "source": "dynamodb",
        }
