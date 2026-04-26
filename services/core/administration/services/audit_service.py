import csv
from io import StringIO

from django.core.paginator import Paginator
from django.db.models import Q

from administration.models import AdminAuditLog
from administration.utils import _parse_datetime_filter


class AuditService:
    @staticmethod
    def get_audit_logs(filters, ordering="-timestamp", page=1, page_size=50):
        """Retrieves and filters administrative action logs."""
        logs = AdminAuditLog.objects.select_related("admin", "target_user").all()

        action = (filters.get("action") or "").strip()
        admin_username = (filters.get("admin") or "").strip()
        target_username = (filters.get("target") or "").strip()
        search = (filters.get("search") or "").strip()

        date_from = _parse_datetime_filter(filters.get("date_from"))
        date_to = _parse_datetime_filter(filters.get("date_to"), end_of_day=True)

        if action:
            logs = logs.filter(action=action)
        if admin_username:
            logs = logs.filter(admin_username__icontains=admin_username)
        if target_username:
            logs = logs.filter(target_username__icontains=target_username)
        if search:
            logs = logs.filter(
                Q(action__icontains=search)
                | Q(admin_username__icontains=search)
                | Q(target_username__icontains=search)
                | Q(request_id__icontains=search)
            )
        if date_from:
            logs = logs.filter(timestamp__gte=date_from)
        if date_to:
            logs = logs.filter(timestamp__lte=date_to)

        allowed_ordering = {
            "timestamp",
            "-timestamp",
            "action",
            "-action",
            "admin_username",
            "-admin_username",
            "target_username",
            "-target_username",
        }
        if ordering not in allowed_ordering:
            ordering = "-timestamp"
        tie_breaker = "-id" if ordering.startswith("-") else "id"
        logs = logs.order_by(ordering, tie_breaker)

        paginator = Paginator(logs, page_size)
        page_obj = paginator.get_page(page)

        return {
            "count": paginator.count,
            "page": page_obj.number,
            "page_size": page_size,
            "total_pages": paginator.num_pages,
            "results": page_obj.object_list,
        }

    @staticmethod
    def generate_audit_logs_csv(filters, ordering="-timestamp"):
        """Generates a CSV string of audit logs."""
        # Note: In a real app, this should probably use streaming, but we'll follow the current pattern.
        logs_data = AuditService.get_audit_logs(filters, ordering, page=1, page_size=1000)
        logs = logs_data["results"]

        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["timestamp", "admin", "action", "target", "request_id", "details"])
        for log in logs:
            writer.writerow(
                [
                    log.timestamp.isoformat(),
                    log.admin_username,
                    log.action,
                    log.target_username,
                    log.request_id,
                    log.details,
                ]
            )
        return buffer.getvalue()
