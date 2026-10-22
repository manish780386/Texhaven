import logging

import requests
from django.conf import settings

log = logging.getLogger(__name__)


def flagged_urls(urls: list[str]) -> set[str]:
    """Return the subset of urls that Google Safe Browsing lists as dangerous. Fails open."""
    key = settings.GOOGLE_SAFE_BROWSING_API_KEY
    if not key or not urls:
        return set()
    try:
        resp = requests.post(
            "https://safebrowsing.googleapis.com/v4/threatMatches:find",
            params={"key": key},
            json={
                "client": {"clientId": "texhaven", "clientVersion": "1.0"},
                "threatInfo": {
                    "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": u if "://" in u else "http://" + u} for u in urls],
                },
            },
            timeout=4,
        )
        resp.raise_for_status()
        hits = {m["threat"]["url"] for m in resp.json().get("matches", [])}
        return {u for u in urls if (u if "://" in u else "http://" + u) in hits}
    except Exception:
        log.warning("safe browsing unavailable")
        return set()
