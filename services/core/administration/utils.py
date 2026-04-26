import uuid
from datetime import datetime, time
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from administration.models import AdminAuditLog

def _request_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

def _request_id(request):
    return request.headers.get("X-Request-ID") or str(uuid.uuid4())

def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return False

def _parse_int(value, default, min_value=None, max_value=None):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if min_value is not None:
        parsed = max(min_value, parsed)
    if max_value is not None:
        parsed = min(max_value, parsed)
    return parsed

def _parse_datetime_filter(value, end_of_day=False):
    if not value:
        return None
    dt = parse_datetime(value)
    if dt:
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt
    d = parse_date(value)
    if not d:
        return None
    if end_of_day:
        dt = datetime.combine(d, time.max).replace(microsecond=0)
    else:
        dt = datetime.combine(d, time.min)
    return timezone.make_aware(dt, timezone.get_current_timezone())

def _analytics_cache_key(prefix, request):
    return f"admin_analytics:{prefix}:{request.get_full_path()}"

def log_admin_action(admin, action, request=None, target_user=None, details=None, target_username=None, target_email=None):
    """Helper to record administrative actions in the audit log."""
    AdminAuditLog.objects.create(
        admin=admin,
        admin_username=admin.username if admin else "system",
        action=action,
        target_user=target_user,
        target_username=target_username or (target_user.username if target_user else ""),
        target_email=target_email or (target_user.email if target_user else ""),
        details=details or {},
        actor_ip=_request_ip(request) if request else None,
        user_agent=(request.headers.get("User-Agent", "")[:512] if request else ""),
        request_id=_request_id(request) if request else "",
    )

def _role_for_user(user):
    if user.is_superuser:
        return "superuser"
    if user.is_staff:
        return "staff"
    return "user"
