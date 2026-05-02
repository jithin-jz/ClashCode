import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import aioboto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DynamoClient:
    def __init__(self):
        self.session = aioboto3.Session()
        self.endpoint_url = os.getenv("DYNAMODB_URL")
        self.region_name = os.getenv("AWS_REGION", "ap-south-1")
        self.table_name = os.getenv("DYNAMODB_TABLE", "ChatMessages")
        self._timestamp_key_type: str | None = None

        self.creds = {"region_name": self.region_name}

        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        session_token = os.getenv("AWS_SESSION_TOKEN")

        if self.endpoint_url:
            self.creds["endpoint_url"] = self.endpoint_url
            if access_key and access_key != "dummy":
                self.creds["aws_access_key_id"] = access_key
            if secret_key and secret_key != "dummy":
                self.creds["aws_secret_access_key"] = secret_key
            if session_token and session_token != "dummy":
                self.creds["aws_session_token"] = session_token
            logger.info(f"DynamoDB connecting to local endpoint: {self.endpoint_url}")
        else:
            # Check for dummy keys even when endpoint_url is not set (production)
            # This ensures IAM role authentication is not blocked by dummy values.
            if access_key and access_key != "dummy" and secret_key and secret_key != "dummy":
                self.creds["aws_access_key_id"] = access_key
                self.creds["aws_secret_access_key"] = secret_key
                if session_token and session_token != "dummy":
                    self.creds["aws_session_token"] = session_token
                logger.info("DynamoDB connecting with explicit AWS credentials")
            else:
                logger.info("DynamoDB connecting via IAM/Default chain")

    async def create_table_if_not_exists(self):
        try:
            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                # Check if ChatMessages table exists
                tables = await dynamo.tables.all()
                table_names = [t.name async for t in tables]
                if self.table_name not in table_names:
                    await dynamo.create_table(
                        TableName=self.table_name,
                        KeySchema=[
                            {"AttributeName": "room_id", "KeyType": "HASH"},
                            {"AttributeName": "timestamp", "KeyType": "RANGE"},
                        ],
                        AttributeDefinitions=[
                            {"AttributeName": "room_id", "AttributeType": "S"},
                            {"AttributeName": "timestamp", "AttributeType": "N"},
                        ],
                        ProvisionedThroughput={
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5,
                        },
                    )
                    logger.info("Table %s created.", self.table_name)
                if "UserActivity" not in table_names:
                    await dynamo.create_table(
                        TableName="UserActivity",
                        KeySchema=[
                            {"AttributeName": "user_id", "KeyType": "HASH"},
                            {"AttributeName": "date", "KeyType": "RANGE"},
                        ],
                        AttributeDefinitions=[
                            {"AttributeName": "user_id", "AttributeType": "S"},
                            {"AttributeName": "date", "AttributeType": "S"},
                        ],
                        ProvisionedThroughput={
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5,
                        },
                    )
                    logger.info("Table UserActivity created.")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "ResourceInUseException":
                logger.info("Table already exists.")
            else:
                logger.exception("Error creating table: %s", e)
        except Exception as e:
            logger.exception("Error creating table: %s", e)

    async def _get_timestamp_key_type(self) -> str:
        if self._timestamp_key_type:
            return self._timestamp_key_type

        try:
            async with self.session.client("dynamodb", **self.creds) as client:
                response = await client.describe_table(TableName=self.table_name)
            attributes = {
                item["AttributeName"]: item["AttributeType"]
                for item in response.get("Table", {}).get("AttributeDefinitions", [])
            }
            self._timestamp_key_type = attributes.get("timestamp", "N")
        except Exception as e:
            logger.warning("Could not inspect DynamoDB timestamp key type, defaulting to numeric: %s", e)
            self._timestamp_key_type = "N"

        return self._timestamp_key_type

    @staticmethod
    def _timestamp_to_epoch_ms(timestamp: Any) -> Decimal:
        if isinstance(timestamp, Decimal):
            return timestamp
        if isinstance(timestamp, int):
            return Decimal(timestamp)
        if isinstance(timestamp, float):
            return Decimal(str(int(timestamp)))

        raw = str(timestamp).strip()
        try:
            return Decimal(raw)
        except Exception:
            pass

        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return Decimal(int(dt.timestamp() * 1000))

    async def _db_timestamp(self, timestamp: Any) -> str | Decimal:
        key_type = await self._get_timestamp_key_type()
        if key_type == "N":
            return self._timestamp_to_epoch_ms(timestamp)
        return str(timestamp)

    @staticmethod
    def _format_db_timestamp(timestamp: Any) -> str:
        if isinstance(timestamp, Decimal):
            return str(int(timestamp)) if timestamp % 1 == 0 else str(timestamp)
        return str(timestamp)

    @staticmethod
    def _timestamp_from_epoch(value: Decimal) -> str:
        divisor = Decimal(1000) if abs(value) > Decimal("100000000000") else Decimal(1)
        seconds = float(value / divisor)
        return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()

    def _client_timestamp(self, item: dict[str, Any]) -> str | None:
        timestamp = item.get("created_at") or item.get("iso_timestamp")
        if timestamp:
            return str(timestamp)

        db_timestamp = item.get("timestamp")
        if db_timestamp is None:
            return None
        if isinstance(db_timestamp, Decimal):
            return self._timestamp_from_epoch(db_timestamp)
        return str(db_timestamp)

    async def save_message(
        self,
        room_id: str,
        sender: str,
        message: str,
        user_id: str = None,
        avatar_url: str = None,
        timestamp: str = None,
        msg_id: str = None,
        reactions: dict | None = None,
        increment_activity: bool = True,
    ):
        actual_timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        try:
            db_timestamp = await self._db_timestamp(actual_timestamp)
            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(self.table_name)
                item = {
                    "room_id": room_id,
                    "timestamp": db_timestamp,
                    "created_at": actual_timestamp,
                    "sender": sender,
                    "content": message,
                }
                if msg_id:
                    item["id"] = msg_id
                if user_id is not None:
                    item["user_id"] = user_id
                if avatar_url:
                    item["avatar_url"] = avatar_url
                if reactions:
                    item["reactions"] = reactions

                await table.put_item(Item=item)

            # Log contribution if user_id provided. Chat persistence should not fail
            # just because the optional activity counter is unavailable.
            if user_id is not None and increment_activity:
                try:
                    async with self.session.resource("dynamodb", **self.creds) as dynamo:
                        activity_table = await dynamo.Table("UserActivity")
                        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                        await activity_table.update_item(
                            Key={"user_id": str(user_id), "date": today},
                            UpdateExpression="ADD contribution_count :inc",
                            ExpressionAttributeValues={":inc": 1},
                        )
                except Exception as ae:
                    logger.warning("Could not update chat activity counter: %s", ae)

            return {"ok": True, "actual_timestamp": actual_timestamp}

        except ClientError as ce:
            error_code = ce.response.get("Error", {}).get("Code", "Unknown")
            logger.exception("DynamoDB ClientError saving message: %s", ce)
            return {"ok": False, "reason": f"db_error_{error_code}"}
        except Exception as e:
            logger.exception("Error saving message to DynamoDB: %s", e)
            return {"ok": False, "reason": f"save_failed: {str(e)[:50]}"}

    async def get_messages(self, room_id: str, limit: int = 100, last_timestamp: str | None = None):
        try:
            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(self.table_name)
                query_kwargs = {
                    "KeyConditionExpression": Key("room_id").eq(room_id),
                    "ScanIndexForward": False,  # Get latest first
                    "Limit": limit,
                }
                if last_timestamp:
                    query_kwargs["ExclusiveStartKey"] = {
                        "room_id": room_id,
                        "timestamp": await self._db_timestamp(last_timestamp),
                    }

                response = await table.query(**query_kwargs)
                last_key = response.get("LastEvaluatedKey")
                if last_key and "timestamp" in last_key:
                    last_key = {
                        **last_key,
                        "timestamp": self._format_db_timestamp(last_key["timestamp"]),
                    }
                return {
                    "items": response.get("Items", []),
                    "last_evaluated_key": last_key,
                }
        except Exception as e:
            logger.exception("Error fetching messages from DynamoDB: %s", e)
            return {"items": [], "last_evaluated_key": None}

    async def get_message(self, room_id: str, timestamp: str) -> dict[str, Any] | None:
        """
        Retrieves a message by room_id and timestamp.
        Includes robust matching for different ISO formats (e.g. with/without Z, offsets, or trailing zeros).
        """
        try:
            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(self.table_name)
                db_timestamp = await self._db_timestamp(timestamp)

                # 1. Try exact match first
                response = await table.get_item(
                    Key={"room_id": room_id, "timestamp": db_timestamp},
                    ConsistentRead=True,
                )
                item = response.get("Item")
                if item:
                    return item

                # 2. Try normalized match
                logger.warning(f"get_message exact match failed for {timestamp!r}. Trying query fallback...")

                alt_ts = None
                raw_timestamp = str(timestamp)
                if raw_timestamp.endswith("Z"):
                    alt_ts = raw_timestamp.replace("Z", "+00:00")
                elif "+00:00" in raw_timestamp:
                    alt_ts = raw_timestamp.replace("+00:00", "Z")

                if alt_ts:
                    response = await table.get_item(
                        Key={"room_id": room_id, "timestamp": await self._db_timestamp(alt_ts)},
                        ConsistentRead=True,
                    )
                    item = response.get("Item")
                    if item:
                        return item

                # 3. Last resort: Query messages in the room and look for a matching prefix
                query_resp = await table.query(
                    KeyConditionExpression=Key("room_id").eq(room_id),
                    ScanIndexForward=False,
                    Limit=20,
                )
                existing = query_resp.get("Items", [])

                for ex in existing:
                    ex_ts = self._client_timestamp(ex) or self._format_db_timestamp(ex.get("timestamp", ""))
                    if ex_ts.startswith(raw_timestamp) or raw_timestamp.startswith(ex_ts):
                        return ex

                logger.error(f"get_message failed even with fuzzy matching for room={room_id} ts={timestamp!r}")
                return None
        except Exception as e:
            logger.exception("Error fetching message from DynamoDB: %s", e)
            return None

    async def edit_message(self, room_id: str, timestamp: str, user_id: int, new_message: str):
        try:
            item = await self.get_message(room_id, timestamp)
            if not item:
                return {"ok": False, "reason": "not_found"}

            db_user_id = item.get("user_id")
            db_timestamp = item.get("timestamp")
            actual_timestamp = self._client_timestamp(item)

            if str(db_user_id) != str(user_id):
                return {"ok": False, "reason": "forbidden"}

            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(self.table_name)
                await table.update_item(
                    Key={"room_id": room_id, "timestamp": db_timestamp},
                    UpdateExpression="SET content = :msg",
                    ExpressionAttributeValues={":msg": new_message},
                )
            return {"ok": True, "actual_timestamp": actual_timestamp}
        except Exception as e:
            logger.exception("Error editing message in DynamoDB: %s", e)
            return {"ok": False, "reason": "error"}

    async def delete_message(self, room_id: str, timestamp: str, user_id: int):
        try:
            item = await self.get_message(room_id, timestamp)
            if not item:
                return {"ok": False, "reason": "not_found"}

            db_user_id = item.get("user_id")
            db_timestamp = item.get("timestamp")
            actual_timestamp = self._client_timestamp(item)

            if str(db_user_id) != str(user_id):
                return {"ok": False, "reason": "forbidden"}

            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(self.table_name)
                await table.delete_item(Key={"room_id": room_id, "timestamp": db_timestamp})
            return {"ok": True, "actual_timestamp": actual_timestamp}
        except Exception as e:
            logger.exception("Error deleting message from DynamoDB: %s", e)
            return {"ok": False, "reason": "error"}

    async def toggle_reaction(self, room_id: str, timestamp: str, username: str, emoji: str):
        try:
            item = await self.get_message(room_id, timestamp)
            if not item:
                return {"ok": False, "reason": "not_found", "reactions": {}}

            db_timestamp = item.get("timestamp")
            actual_timestamp = self._client_timestamp(item)
            reactions = item.get("reactions", {})

            users_for_emoji = reactions.get(emoji, [])
            if username in users_for_emoji:
                users_for_emoji.remove(username)
                if not users_for_emoji:
                    reactions.pop(emoji, None)
                else:
                    reactions[emoji] = users_for_emoji
            else:
                users_for_emoji.append(username)
                reactions[emoji] = users_for_emoji

            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(self.table_name)
                await table.update_item(
                    Key={"room_id": room_id, "timestamp": db_timestamp},
                    UpdateExpression="SET reactions = :r",
                    ExpressionAttributeValues={":r": reactions},
                )
            return {"ok": True, "reactions": reactions, "actual_timestamp": actual_timestamp}
        except Exception as e:
            logger.exception("Error toggling reaction in DynamoDB: %s", e)
            return {"ok": False, "reason": "error", "reactions": {}}

    async def mark_as_read(self, room_id: str, timestamp: str, username: str):
        try:
            item = await self.get_message(room_id, timestamp)
            if not item:
                return {"ok": False, "reason": "not_found"}

            db_timestamp = item.get("timestamp")
            actual_timestamp = self._client_timestamp(item)

            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(self.table_name)
                try:
                    await table.update_item(
                        Key={"room_id": room_id, "timestamp": db_timestamp},
                        UpdateExpression="ADD read_by :u",
                        ExpressionAttributeValues={":u": {username}},
                    )
                except ClientError as ce:
                    if ce.response.get("Error", {}).get("Code") == "ValidationException":
                        logger.warning(f"Attribute type mismatch for read_by, attempting fallback to SET for {db_timestamp}")
                    raise ce
            return {"ok": True, "actual_timestamp": actual_timestamp}
        except Exception as e:
            logger.exception("Error marking message as read in DynamoDB: %s", e)
            return {"ok": False, "reason": "error"}

    async def search_messages(self, room_id: str, query: str, limit: int = 20):
        try:
            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(self.table_name)
                response = await table.query(
                    KeyConditionExpression=Key("room_id").eq(room_id),
                    FilterExpression="contains(content, :q)",
                    ExpressionAttributeValues={":q": query},
                    Limit=limit,
                    ScanIndexForward=False,
                )
                return {"items": response.get("Items", []), "ok": True}
        except Exception as e:
            logger.exception("Error searching messages in DynamoDB: %s", e)
            return {"items": [], "ok": False}


dynamo_client = DynamoClient()
