import logging

from .models import FCMToken, Notification
from .tasks import send_push_notification_task

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Business logic for creating and managing notifications.
    """

    @staticmethod
    def create_notification(recipient, actor, verb, target=None, push=True, push_title=None, push_body=None):
        """
        Creates a notification record and optionally sends a push/WS notification.
        """
        notification = Notification.objects.create(recipient=recipient, actor=actor, verb=verb, target=target)

        if push:
            title = push_title or "New Notification"
            body = push_body or f"{actor.username} {verb}"
            send_push_notification_task.delay(recipient.id, title, body)

        return notification

    @staticmethod
    def mark_as_read(notification_id, user):
        """Marks a single notification as read if it belongs to the user."""
        try:
            notification = Notification.objects.get(id=notification_id, recipient=user)
            if not notification.is_read:
                notification.is_read = True
                notification.save(update_fields=["is_read"])
            return True
        except Notification.DoesNotExist:
            return False

    @staticmethod
    def mark_all_as_read(user):
        """Marks all unread notifications for a user as read."""
        return Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)

    @staticmethod
    def clear_all(user):
        """Deletes all notifications for a user."""
        return Notification.objects.filter(recipient=user).delete()

    @staticmethod
    def register_fcm_token(user, token, device_id=None):
        """Registers or updates an FCM token for a user."""
        fcm_token, created = FCMToken.objects.update_or_create(
            token=token, defaults={"user": user, "device_id": device_id}
        )
        return fcm_token, created
