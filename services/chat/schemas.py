import uuid
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    type: str
    timestamp: str = Field(default_factory=lambda: datetime.now(ZoneInfo("Asia/Kolkata")).isoformat())


class ChatMessage(BaseEvent):
    type: Literal["chat_message"] = "chat_message"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room: str
    message: str = Field(min_length=1, max_length=1000)
    user_id: int
    username: str
    avatar_url: str | None = None


class PresenceEvent(BaseEvent):
    type: Literal["presence"] = "presence"
    event: Literal["join", "leave"]
    user_id: int
    username: str
    avatar_url: str | None = None
    count: int = 0


class IncomingMessage(BaseModel):
    action: Literal["send", "edit", "delete", "typing", "react", "pin", "unpin", "read"] = "send"
    target_timestamp: str | None = None
    message: str | None = Field(None, max_length=1000)
    emoji: str | None = None  # For reactions
    room: str | None = None  # Sent by frontend, but room is taken from URL path
