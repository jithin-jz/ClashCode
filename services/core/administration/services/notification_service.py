from django.contrib.auth.models import User
from notifications.models import Notification

from administration.models import AdminAuditLog
from administration.utils import _parse_bool, log_admin_action


class NotificationService:
    @staticmethod
    def broadcast_notification(admin, message, include_staff, reason, request=None):
        """Broadcasts a notification to all active users."""
        if not message:
            return False, "Message is required", 400

        if len(message) > 500:
            return False, "Message too long (max 500 characters)", 400

        users_qs = User.objects.filter(is_active=True).exclude(id=admin.id)
        if not include_staff:
            users_qs = users_qs.filter(is_staff=False, is_superuser=False)

        recipient_count = users_qs.count()

        def generate_notifications():
            for user_id in users_qs.values_list("id", flat=True).iterator(chunk_size=2000):
                yield Notification(recipient_id=user_id, actor=admin, verb=message)

        Notification.objects.bulk_create(generate_notifications(), batch_size=2000)

        log_admin_action(
            admin=admin,
            action="SEND_GLOBAL_NOTIFICATION",
            request=request,
            details={
                "message": message,
                "recipient_count": recipient_count,
                "include_staff": include_staff,
                "reason": reason,
            },
        )
        return True, f"Broadcast sent to {recipient_count} users", 200

    @staticmethod
    def get_broadcast_history():
        """Retrieves broadcast history from admin audit logs."""
        logs = AdminAuditLog.objects.filter(action="SEND_GLOBAL_NOTIFICATION").order_by("-timestamp")[:25]
        rows = []
        for log in logs:
            rows.append(
                {
                    "request_id": log.request_id,
                    "message": log.details.get("message", ""),
                    "recipient_count": log.details.get("recipient_count", 0),
                    "include_staff": log.details.get("include_staff", False),
                    "reason": log.details.get("reason", ""),
                    "timestamp": log.timestamp.isoformat(),
                    "admin": log.admin_username or (log.admin.username if log.admin else "System"),
                }
            )
        return rows

    @staticmethod
    def resend_broadcast(admin, request_id, request=None):
        """Resends a previously sent broadcast."""
        log = AdminAuditLog.objects.filter(action="SEND_GLOBAL_NOTIFICATION", request_id=request_id).first()
        if not log:
            return False, "Broadcast not found.", 404

        verb = (log.details or {}).get("message")
        if not verb:
            return False, "Broadcast message missing.", 400

        include_staff = _parse_bool((log.details or {}).get("include_staff", False))
        users_qs = User.objects.filter(is_active=True).exclude(id=admin.id)
        if not include_staff:
            users_qs = users_qs.filter(is_staff=False, is_superuser=False)

        recipient_count = users_qs.count()

        def generate_notifications():
            for user_id in users_qs.values_list("id", flat=True).iterator(chunk_size=2000):
                yield Notification(recipient_id=user_id, actor=admin, verb=verb)

        Notification.objects.bulk_create(generate_notifications(), batch_size=2000)

        log_admin_action(
            admin=admin,
            action="RESEND_GLOBAL_NOTIFICATION",
            request=request,
            details={
                "message": verb,
                "recipient_count": recipient_count,
                "source_request_id": request_id,
                "include_staff": include_staff,
            },
        )
        return True, f"Broadcast resent to {recipient_count} users", 200
