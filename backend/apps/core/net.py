from django.conf import settings


def client_ip(request) -> str:
    """Client IP honoring exactly NUM_PROXIES trusted proxies (same logic as DRF's throttle)."""
    remote = request.META.get("REMOTE_ADDR", "0.0.0.0")
    n = settings.NUM_PROXIES
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if not n or not xff:
        return remote
    addrs = [a.strip() for a in xff.split(",") if a.strip()]
    if not addrs:
        return remote
    return addrs[-min(n, len(addrs))]
