import os
import aioboto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from datetime import datetime
import logging
from typing import Any

# Credentials
DYNAMODB_URL = os.getenv("DYNAMODB_URL", "http://dynamodb:8000")
REGION_NAME = os.getenv("AWS_REGION", "ap-south-1")
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "dummy")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "dummy")
TABLE_NAME = "ChatMessages"
logger = logging.getLogger(__name__)


class DynamoClient:
    def __init__(self):
        self.session = aioboto3.Session()
        self.endpoint_url = DYNAMODB_URL
        # Explicit credentials block
        self.creds = {
            "aws_access_key_id": ACCESS_KEY,
            "aws_secret_access_key": SECRET_KEY,
            "region_name": REGION_NAME,
            "endpoint_url": self.endpoint_url,
        }

    async def create_table_if_not_exists(self):
        try:
            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                tables = [table.name async for table in dynamo.tables.all()]
                if TABLE_NAME not in tables:
                    await dynamo.create_table(
                        TableName=TABLE_NAME,
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
                    logger.info("Table %s created.", TABLE_NAME)
                if "UserActivity" not in tables:
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
                table = await dynamo.Table(TABLE_NAME)
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

    async def get_messages(self, room_id: str, limit: int = 50, last_timestamp: str | None = None):
        try:
            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(TABLE_NAME)
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
                    "last_evaluated_key": response.get("LastEvaluatedKey")
                }
        except Exception as e:
            logger.exception("Error fetching messages from DynamoDB: %s", e)
            return {"items": [], "last_evaluated_key": None}

    async def get_message(self, room_id: str, timestamp: str) -> dict[str, Any] | None:
        try:
            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(TABLE_NAME)
                response = await table.get_item(
                    Key={"room_id": room_id, "timestamp": timestamp}
                )
                return response.get("Item")
        except Exception as e:
            logger.exception("Error fetching message from DynamoDB: %s", e)
            return None

    async def edit_message(
        self, room_id: str, timestamp: str, user_id: int, new_message: str
    ):
        try:
            item = await self.get_message(room_id, timestamp)
            if not item:
                return {"ok": False, "reason": "not_found"}
            if str(item.get("user_id")) != str(user_id):
                return {"ok": False, "reason": "forbidden"}

            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(TABLE_NAME)
                await table.update_item(
                    Key={"room_id": room_id, "timestamp": timestamp},
                    UpdateExpression="SET content = :msg",
                    ExpressionAttributeValues={":msg": new_message},
                )
            return {"ok": True}
        except Exception as e:
            logger.exception("Error editing message in DynamoDB: %s", e)
            return {"ok": False, "reason": "error"}

    async def delete_message(self, room_id: str, timestamp: str, user_id: int):
        try:
            item = await self.get_message(room_id, timestamp)
            if not item:
                return {"ok": False, "reason": "not_found"}
            if str(item.get("user_id")) != str(user_id):
                return {"ok": False, "reason": "forbidden"}

            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(TABLE_NAME)
                await table.delete_item(
                    Key={"room_id": room_id, "timestamp": timestamp}
                )
            return {"ok": True}
        except Exception as e:
            logger.exception("Error deleting message from DynamoDB: %s", e)
            return {"ok": False, "reason": "error"}

    async def toggle_reaction(
        self, room_id: str, timestamp: str, username: str, emoji: str
    ):
        """Toggle a user's emoji reaction on a message. If already reacted with same emoji, remove it."""
        try:
            item = await self.get_message(room_id, timestamp)
            if not item:
                return {"ok": False, "reason": "not_found", "reactions": {}}

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
                table = await dynamo.Table(TABLE_NAME)
                await table.update_item(
                    Key={"room_id": room_id, "timestamp": timestamp},
                    UpdateExpression="SET reactions = :r",
                    ExpressionAttributeValues={":r": reactions},
                )
            return {"ok": True, "reactions": reactions}
        except Exception as e:
            logger.exception("Error toggling reaction in DynamoDB: %s", e)
            return {"ok": False, "reason": "error", "reactions": {}}


    async def mark_as_read(self, room_id: str, timestamp: str, username: str):
        """Add a user to the read_by list of a message."""
        try:
            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(TABLE_NAME)
                # Use ADD to insert into a string set (SS) to avoid duplicates efficiently
                # But here we use a list for simplicity or a set if Boto3 allows easily.
                # Actually, DynamoDB UpdateExpression "ADD" works for Sets.
                # Let's use a List and keep it simple for now, or just use a Set attribute.
                await table.update_item(
                    Key={"room_id": room_id, "timestamp": timestamp},
                    UpdateExpression="ADD read_by :u",
                    ExpressionAttributeValues={":u": {username}}, # Set literal
                )
            return {"ok": True}
        except Exception as e:
            logger.exception("Error marking message as read in DynamoDB: %s", e)
            return {"ok": False, "reason": "error"}


    async def search_messages(self, room_id: str, query: str, limit: int = 20):
        """Search messages in a room containing the query string."""
        try:
            async with self.session.resource("dynamodb", **self.creds) as dynamo:
                table = await dynamo.Table(TABLE_NAME)
                # Using scan with FilterExpression for simple substring search
                # This is not highly efficient for large datasets but works for chat search
                response = await table.query(
                    KeyConditionExpression=Key("room_id").eq(room_id),
                    FilterExpression="contains(content, :q)",
                    ExpressionAttributeValues={":q": query},
                    Limit=limit,
                    ScanIndexForward=False # Latest matches first
                )
                return {
                    "items": response.get("Items", []),
                    "ok": True
                }
        except Exception as e:
            logger.exception("Error searching messages in DynamoDB: %s", e)
            return {"items": [], "ok": False}


dynamo_client = DynamoClient()
