import json
from decimal import Decimal
from typing import Any


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o % 1 == 0 else float(o)
        return super().default(o)


def json_dumps(obj: Any) -> str:
    return json.dumps(obj, cls=DecimalEncoder)


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
