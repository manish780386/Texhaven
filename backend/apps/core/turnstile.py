import logging

import requests
from django.conf import settings

log = logging.getLogger(__name__)
VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify(token: str | None, ip: str) -> bool:
    """Verify a Cloudflare Turnstile token. Fails closed on any error."""
    if settings.TURNSTILE_BYPASS:
        return True
    if not token or not settings.TURNSTILE_SECRET_KEY:
        return False
    try:
        resp = requests.post(
            VERIFY_URL,
            data={"secret": settings.TURNSTILE_SECRET_KEY, "response": token, "remoteip": ip},
            timeout=5,
        )
        return resp.json().get("success") is True
    except (requests.RequestException, ValueError):
        log.warning("turnstile verification error")
        return False
