import json
import logging
import os
from pathlib import Path

import redis
from django.conf import settings

from .models import FCMToken

logger = logging.getLogger(__name__)

import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)

# Initialize Redis client for real-time WebSocket notifications
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))

# Initialize Firebase Admin SDK
try:
    if settings.FIREBASE_SERVICE_ACCOUNT_PATH and not firebase_admin._apps:
        firebase_key_path = Path(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        if firebase_key_path.exists():
            cred = credentials.Certificate(str(firebase_key_path))
            firebase_admin.initialize_app(cred)
        else:
            logger.warning(
                "FIREBASE_SERVICE_ACCOUNT_PATH=%s was not found; push notifications are disabled.",
                firebase_key_path,
            )
    elif not settings.FIREBASE_SERVICE_ACCOUNT_PATH:
        logger.warning("FIREBASE_SERVICE_ACCOUNT_PATH is not configured; push notifications are disabled.")
except Exception as e:
    logger.warning(f"Failed to initialize Firebase Admin SDK: {e}")


def notify_via_ws(user_id, data):
    """
    Publishes notification data to Redis for WebSocket broadcasting.
    """
    try:
        channel = f"notifications_{user_id}"
        redis_client.publish(channel, json.dumps(data))
        logger.info(f"Published notification to Redis channel {channel}")
    except Exception as e:
        logger.error(f"Failed to publish notification to Redis: {e}")


def send_fcm_push(user, title, body, data=None):
    """
    Sends a push notification to all devices registered for a user.
    """
    # Also trigger WebSocket notification for immediate UI update
    ws_data = {"type": "notification", "title": title, "body": body, "data": data or {}}
    notify_via_ws(user.id, ws_data)

    tokens = list(FCMToken.objects.filter(user=user).values_list("token", flat=True))

    if not tokens:
        logger.info(f"No FCM tokens found for user {user.username}")
        return

    if not firebase_admin._apps:
        logger.warning("Firebase not initialized; push delivery may fail for %s", user.username)

    try:
        # Move notification details into data to give SW full control
        # and prevent double-show from browser native handler.
        fcm_data = data.copy() if data else {}
        fcm_data.update(
            {
                "title": str(title),
                "body": str(body),
                "icon": "/favicon.png",
            }
        )

        message = messaging.MulticastMessage(
            data=fcm_data,
            tokens=tokens,
        )
        response = messaging.send_each_for_multicast(message)
        logger.info(f"Successfully sent FCM push to {user.username}: {response.success_count} success, {response.failure_count} failure")

        # Optional: Clean up failed tokens
        if response.failure_count > 0:
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    # Token might be invalid or expired
                    failed_token = tokens[idx]
                    FCMToken.objects.filter(token=failed_token).delete()
                    logger.info(f"Deleted invalid FCM token for {user.username}")

    except Exception as e:
        logger.error(f"Error sending FCM push to {user.username}: {e}")
