from challenges.models import Challenge
from django.contrib.auth.models import User
from django.core.cache import cache
from notifications.models import Notification
from store.models import StoreItem

from administration.models import AdminAuditLog, AdminReport


class SystemService:
    CACHE_TTL = 60 * 2  # 2 minutes

    @staticmethod
    def get_system_integrity():
        """Get collection counts for key models with caching."""
        cache_key = "admin:system:integrity"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        data = {
            "users": User.objects.count(),
            "challenges": Challenge.objects.count(),
            "store_items": StoreItem.objects.count(),
            "notifications": Notification.objects.count(),
            "audit_logs": AdminAuditLog.objects.count(),
        }
        cache.set(cache_key, data, timeout=SystemService.CACHE_TTL)
        return data

    @staticmethod
    def get_system_health():
        """Get lightweight operational health data with caching."""
        cache_key = "admin:system:health"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        latest_audit = AdminAuditLog.objects.order_by("-timestamp").values_list("timestamp", flat=True).first()
        latest_broadcast = (
            AdminAuditLog.objects.filter(action="SEND_GLOBAL_NOTIFICATION")
            .order_by("-timestamp")
            .values_list("timestamp", flat=True)
            .first()
        )
        data = {
            "database": "online",
            "authentication": "online",
            "notifications": "online",
            "audit_pipeline": "active",
            "latest_audit_at": latest_audit.isoformat() if latest_audit else None,
            "latest_broadcast_at": (latest_broadcast.isoformat() if latest_broadcast else None),
            "open_reports": AdminReport.objects.exclude(status=AdminReport.Status.RESOLVED).count(),
        }
        cache.set(cache_key, data, timeout=SystemService.CACHE_TTL)
        return data
