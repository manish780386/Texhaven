"""Business logic: validate, scan, rate-limit and create a message awaiting payment."""
import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.core import ratelimit
from apps.core.crypto import encrypt, hash_value, new_token
from apps.scanner.engine import scan

from . import payments
from .models import AuditLog, Blocklist, Message
from .utils import NumberError, build_sms_text, clean_body, normalize_number, price_for, sms_info

log = logging.getLogger(__name__)


class Rejected(Exception):
    def __init__(self, code: str, detail: str, http_status: int = 422, extra: dict | None = None):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.http_status = http_status
        self.extra = extra or {}


def audit(event: str, message_id=None, **meta):
    AuditLog.objects.create(event=event, message_id=message_id, meta=meta)


def block_number(to_hash: str, source: str) -> bool:
    _, created = Blocklist.objects.get_or_create(to_hash=to_hash, defaults={"source": source})
    return created


def create_message(*, raw_to: str, body: str, ip: str) -> tuple[Message, str]:
    """Returns (message, checkout_url). Raises Rejected."""
    if not settings.SMS_ENABLED:
        raise Rejected("sms_disabled", "Sending is not open yet. Join the waitlist.", 503)

    body = clean_body(body)
    if not body:
        raise Rejected("empty", "Write a message first.", 400)

    try:
        e164, region, masked = normalize_number(raw_to)
    except NumberError as exc:
        raise Rejected("bad_number", str(exc), 400)
    if region in settings.BLOCKED_COUNTRIES:
        raise Rejected("country_blocked", "Texhaven cannot send to this country yet.", 422)

    to_hash = hash_value(e164)
    ip_hash = hash_value(ip)

    if Blocklist.objects.filter(to_hash=to_hash).exists():
        audit("blocked_recipient_attempt", ip=ip_hash[:12])
        raise Rejected("recipient_unavailable", "This recipient cannot receive messages from Texhaven.", 422)

    if not ratelimit.hit(f"rl:to:{to_hash}", settings.DAILY_LIMIT_PER_RECIPIENT, 86400):
        raise Rejected("recipient_limit", "This number has received the maximum messages for today.", 429)
    if not ratelimit.hit(f"rl:ip:{ip_hash}", settings.DAILY_LIMIT_PER_IP, 86400):
        raise Rejected("sender_limit", "You have reached today's sending limit.", 429)

    result = scan(body)
    if result.score >= settings.BLOCK_THRESHOLD:
        audit("message_rejected", score=result.score, categories=result.categories, ip=ip_hash[:12])
        raise Rejected(
            "unsafe",
            "This message looks unsafe, so Texhaven will not send it.",
            422,
            {"reasons": [r["label"] for r in result.reasons][:5], "score": result.score},
        )

    optout = new_token()
    info = sms_info(build_sms_text(body, optout))
    if info.segments > settings.MAX_SEGMENTS:
        raise Rejected("too_long", f"Message is too long (max {settings.MAX_SEGMENTS} segments).", 400)

    now = timezone.now()
    with transaction.atomic():
        msg = Message.objects.create(
            track_id=new_token(),
            optout_token=optout,
            to_enc=encrypt(e164),
            body_enc=encrypt(body),
            to_hash=to_hash,
            to_masked=masked,
            to_country=region,
            segments=info.segments,
            encoding=info.encoding,
            price_cents=price_for(info.segments),
            currency=settings.CURRENCY,
            risk_score=result.score,
            risk_categories=result.categories,
            sender_ip_hash=ip_hash,
            expires_at=now + timedelta(hours=settings.MESSAGE_TTL_HOURS),
        )
    audit("message_created", msg.id, segments=info.segments, country=region, score=result.score)
    return msg, payments.create_checkout(msg)
