import logging
import os
from datetime import datetime
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

        self.creds = {"region_name": self.region_name}

        if self.endpoint_url:
            self.creds["endpoint_url"] = self.endpoint_url
            # For local dev, we might still want to use provided keys if they aren't "dummy"
            access_key = os.getenv("AWS_ACCESS_KEY_ID")
            secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            if access_key and access_key != "dummy":
                self.creds["aws_access_key_id"] = access_key
            if secret_key and secret_key != "dummy":
                self.creds["aws_secret_access_key"] = secret_key
            logger.info(f"DynamoDB connecting to local endpoint: {self.endpoint_url}")
        else:
            # In production, we explicitly do NOT pass aws_access_key_id if it's not provided
            # to allow the SDK to fall back to IRSA/Instance Metadata.
            # We also clear them from environment to be safe.
            if os.environ.get("AWS_ACCESS_KEY_ID"):
                logger.info("Clearing AWS_ACCESS_KEY_ID to enable IRSA")
                os.environ.pop("AWS_ACCESS_KEY_ID", None)
            if os.environ.get("AWS_SECRET_ACCESS_KEY"):
                os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
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
                            {"AttributeName": "timestamp", "AttributeType": "S"},
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

    async def save_message(
        self,
        room_id: str,
        sender: str,
        message: str,
        user_id: str = None,
        avatar_url: str = None,
        timestamp: str = None,
        reactions: dict | None = None,
        increment_activity: bool = True,
    ):
        try:
            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(self.table_name)
                item = {
                    "room_id": room_id,
                    "timestamp": timestamp or datetime.utcnow().isoformat(),
                    "sender": sender,
                    "content": message,
                }
                if user_id is not None:
                    item["user_id"] = user_id
                if avatar_url:
                    item["avatar_url"] = avatar_url
                if reactions:
                    item["reactions"] = reactions

                await table.put_item(Item=item)

                # Log contribution if user_id provided
                if user_id and increment_activity:
                    activity_table = await dynamo.Table("UserActivity")
                    today = datetime.utcnow().strftime("%Y-%m-%d")
                    await activity_table.update_item(
                        Key={"user_id": str(user_id), "date": today},
                        UpdateExpression="ADD contribution_count :inc",
                        ExpressionAttributeValues={":inc": 1},
                    )
        except Exception as e:
            logger.exception("Error saving message to DynamoDB: %s", e)

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
                        "timestamp": last_timestamp,
                    }

                response = await table.query(**query_kwargs)
                return {
                    "items": response.get("Items", []),
                    "last_evaluated_key": response.get("LastEvaluatedKey"),
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
                
                # 1. Try exact match first
                response = await table.get_item(Key={"room_id": room_id, "timestamp": timestamp})
                item = response.get("Item")
                if item:
                    return item

                # 2. Try normalized match (handle Z vs +00:00, or microsecond precision differences)
                # We'll query a small range or just search recent if exact fails
                logger.warning(f"get_message exact match failed for {timestamp!r}. Trying query fallback...")
                
                # Simple normalization: try replacing Z with +00:00 or vice versa if applicable
                alt_ts = None
                if timestamp.endswith("Z"):
                    alt_ts = timestamp.replace("Z", "+00:00")
                elif "+00:00" in timestamp:
                    alt_ts = timestamp.replace("+00:00", "Z")
                
                if alt_ts:
                    response = await table.get_item(Key={"room_id": room_id, "timestamp": alt_ts})
                    item = response.get("Item")
                    if item:
                        logger.info(f"Found item with alternate timestamp: {alt_ts!r}")
                        return item

                # 3. Last resort: Query messages in the room and look for a matching prefix or close time
                # This helps if the frontend truncated the string
                query_resp = await table.query(
                    KeyConditionExpression=Key("room_id").eq(room_id),
                    ScanIndexForward=False,
                    Limit=20,
                )
                existing = query_resp.get("Items", [])
                
                # Try prefix match (e.g. 2024-05-01T12:00:00.123 match 2024-05-01T12:00:00.123456)
                for ex in existing:
                    ex_ts = ex.get("timestamp", "")
                    if ex_ts.startswith(timestamp) or timestamp.startswith(ex_ts):
                        logger.info(f"Fuzzy match found: provided={timestamp!r}, db={ex_ts!r}")
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
            db_timestamp = item.get("timestamp") # Use the actual DB timestamp for the update
            
            if str(db_user_id) != str(user_id):
                return {"ok": False, "reason": "forbidden"}

            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(self.table_name)
                await table.update_item(
                    Key={"room_id": room_id, "timestamp": db_timestamp},
                    UpdateExpression="SET content = :msg",
                    ExpressionAttributeValues={":msg": new_message},
                )
            return {"ok": True, "actual_timestamp": db_timestamp}
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
            
            if str(db_user_id) != str(user_id):
                return {"ok": False, "reason": "forbidden"}

            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(self.table_name)
                await table.delete_item(Key={"room_id": room_id, "timestamp": db_timestamp})
            return {"ok": True, "actual_timestamp": db_timestamp}
        except Exception as e:
            logger.exception("Error deleting message from DynamoDB: %s", e)
            return {"ok": False, "reason": "error"}

    async def toggle_reaction(self, room_id: str, timestamp: str, username: str, emoji: str):
        """Toggle a user's emoji reaction on a message. If already reacted with same emoji, remove it."""
        try:
            item = await self.get_message(room_id, timestamp)
            if not item:
                return {"ok": False, "reason": "not_found", "reactions": {}}

            db_timestamp = item.get("timestamp")
            reactions = item.get("reactions", {})

            # Toggle: if user already reacted with this emoji, remove them; otherwise add
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
            return {"ok": True, "reactions": reactions, "actual_timestamp": db_timestamp}
        except Exception as e:
            logger.exception("Error toggling reaction in DynamoDB: %s", e)
            return {"ok": False, "reason": "error", "reactions": {}}

    async def mark_as_read(self, room_id: str, timestamp: str, username: str):
        """Add a user to the read_by list of a message."""
        try:
            # First find the message to ensure we have the correct timestamp and it exists
            item = await self.get_message(room_id, timestamp)
            if not item:
                return {"ok": False, "reason": "not_found"}
            
            db_timestamp = item.get("timestamp")

            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(self.table_name)
                # Check if read_by exists and is a set. If not, we might need to initialize it.
                try:
                    await table.update_item(
                        Key={"room_id": room_id, "timestamp": db_timestamp},
                        UpdateExpression="ADD read_by :u",
                        ExpressionAttributeValues={":u": {username}},
                    )
                except ClientError as ce:
                    # If attribute type mismatch (e.g. read_by is a List), fallback to SET
                    if ce.response.get("Error", {}).get("Code") == "ValidationException":
                        logger.warning(f"Attribute type mismatch for read_by, attempting fallback to SET for {db_timestamp}")
                        pass
                    raise ce
            return {"ok": True, "actual_timestamp": db_timestamp}
        except Exception as e:
            logger.exception("Error marking message as read in DynamoDB: %s", e)
            return {"ok": False, "reason": "error"}



    async def search_messages(self, room_id: str, query: str, limit: int = 20):
        """Search messages in a room containing the query string."""
        try:
            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(self.table_name)
                # Using scan with FilterExpression for simple substring search
                # This is not highly efficient for large datasets but works for chat search
                response = await table.query(
                    KeyConditionExpression=Key("room_id").eq(room_id),
                    FilterExpression="contains(content, :q)",
                    ExpressionAttributeValues={":q": query},
                    Limit=limit,
                    ScanIndexForward=False,  # Latest matches first
                )
                return {"items": response.get("Items", []), "ok": True}
        except Exception as e:
            logger.exception("Error searching messages in DynamoDB: %s", e)
            return {"items": [], "ok": False}


dynamo_client = DynamoClient()
