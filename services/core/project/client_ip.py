from rest_framework.settings import api_settings


def get_client_ip(request) -> str | None:
    """
    The real client IP, using the same rule as DRF throttling.

    Only the last NUM_PROXIES entries of X-Forwarded-For were written by proxies
    we run; everything before them is client-controlled and must not be trusted
    for rate limits or audit logs.
    """
    remote_addr = request.META.get("REMOTE_ADDR")
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    num_proxies = api_settings.NUM_PROXIES

    if num_proxies is None or num_proxies == 0 or not xff:
        return remote_addr

    addrs = [addr.strip() for addr in xff.split(",") if addr.strip()]
    if not addrs:
        return remote_addr
    return addrs[-min(num_proxies, len(addrs))]
