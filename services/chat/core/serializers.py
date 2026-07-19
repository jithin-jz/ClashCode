import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o % 1 == 0 else float(o)
        return super().default(o)


def json_dumps(obj: Any) -> str:
    return json.dumps(obj, cls=DecimalEncoder)


def serialize_timestamp(value: Any) -> Any:
    if not isinstance(value, Decimal):
        return value

    divisor = Decimal(1000) if abs(value) > Decimal("100000000000") else Decimal(1)
    return datetime.fromtimestamp(float(value / divisor), tz=UTC).isoformat()


def decimal_to_json(obj: Any) -> Any:
    """Recursively convert Decimal objects to int or float."""
    if isinstance(obj, list):
        return [decimal_to_json(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_json(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


def serialize_dynamo_message(room: str, item: dict) -> dict:
    """Safely serialize a DynamoDB item for the frontend."""
    timestamp = item.get("created_at") or item.get("iso_timestamp") or item.get("timestamp")
    return decimal_to_json(
        {
            "room": room,
            "message": item.get("content", ""),
            "user_id": item.get("user_id"),
            "username": item.get("sender") or item.get("username") or "Unknown",
            "avatar_url": item.get("avatar_url"),
            "timestamp": serialize_timestamp(timestamp),
            "reactions": item.get("reactions", {}),
        }
    )
