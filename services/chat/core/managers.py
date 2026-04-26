import asyncio
import json
import logging
from typing import Dict, List

from fastapi import WebSocket
from utils.redis_client import channel_key, redis_client

from core.serializers import json_dumps

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, List[WebSocket]] = {}
        self.tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, ws: WebSocket, room: str):
        await ws.accept()
        self.active.setdefault(room, []).append(ws)

        if len(self.active[room]) == 1 and room not in self.tasks:
            self.tasks[room] = asyncio.create_task(self.redis_subscriber(room))

    async def disconnect(self, ws: WebSocket, room: str):
        if room in self.active and ws in self.active[room]:
            self.active[room].remove(ws)

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
            except Exception as e:
                logger.error(f"Error broadcasting to room {room}: {e}")
                dead.append(ws)

        for ws in dead:
            await self.disconnect(ws, room)


class NotificationManager:
    def __init__(self):
        self.active: Dict[int, List[WebSocket]] = {}
        self.tasks: Dict[int, asyncio.Task] = {}

    async def connect(self, ws: WebSocket, user_id: int):
        await ws.accept()
        self.active.setdefault(user_id, []).append(ws)

        if len(self.active[user_id]) == 1 and user_id not in self.tasks:
            self.tasks[user_id] = asyncio.create_task(self.notification_subscriber(user_id))
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


manager = ConnectionManager()
notification_manager = NotificationManager()
