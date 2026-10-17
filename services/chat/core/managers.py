import asyncio
import contextlib
import json
import logging

from fastapi import WebSocket

from core.serializers import json_dumps
from utils.redis_client import channel_key, redis_client

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}
        self.tasks: dict[str, asyncio.Task] = {}

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
                    with contextlib.suppress(asyncio.CancelledError):
                        await self.tasks[room]
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
    """
    Per-user push (task results, notifications).

    One Redis pattern subscription per process, shared by every connected user,
    instead of one Redis connection per online user.
    """

    CHANNEL_PATTERN = "notifications_*"
    _RESTART_DELAY_SECONDS = 1.0

    def __init__(self):
        self.active: dict[int, list[WebSocket]] = {}
        self._task: asyncio.Task | None = None

    async def connect(self, ws: WebSocket, user_id: int):
        await ws.accept()
        self.active.setdefault(user_id, []).append(ws)

        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run_subscriber())
            logger.info("Started shared notification subscriber")

    async def disconnect(self, ws: WebSocket, user_id: int):
        if user_id in self.active and ws in self.active[user_id]:
            self.active[user_id].remove(ws)
            if not self.active[user_id]:
                self.active.pop(user_id, None)

        if not self.active and self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
            logger.info("Stopped shared notification subscriber")

    @staticmethod
    def _user_id_from_channel(channel) -> int | None:
        if isinstance(channel, bytes):
            channel = channel.decode()
        try:
            return int(str(channel).rsplit("_", 1)[1])
        except (IndexError, ValueError):
            return None

    async def _run_subscriber(self):
        # Keep a single subscription alive while anyone is connected; reconnect on Redis errors.
        while self.active:
            try:
                await self.notification_subscriber()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Notification subscriber failed, restarting: {e}")
                await asyncio.sleep(self._RESTART_DELAY_SECONDS)

    async def notification_subscriber(self):
        pubsub = redis_client.pubsub()
        await pubsub.psubscribe(self.CHANNEL_PATTERN)
        try:
            async for event in pubsub.listen():
                if event["type"] != "pmessage":
                    continue
                user_id = self._user_id_from_channel(event["channel"])
                if user_id is None or user_id not in self.active:
                    continue
                await self.broadcast_user(user_id, json.loads(event["data"]))
        finally:
            with contextlib.suppress(Exception):
                await pubsub.punsubscribe(self.CHANNEL_PATTERN)
                await pubsub.aclose()

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
