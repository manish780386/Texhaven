import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.core.crypto import decrypt

from . import payments
from .models import Message
from .providers import SmsError, send_sms
from .services import audit
from .utils import build_sms_text

log = logging.getLogger(__name__)


def mark_paid(message_id: str, payment_intent: str = "") -> bool:
    """Idempotently move awaiting_payment -> paid and queue the SMS. Returns True if it changed."""
    with transaction.atomic():
        msg = Message.objects.select_for_update().get(pk=message_id)
        if msg.status != Message.Status.AWAITING_PAYMENT:
            return False
        msg.status = Message.Status.PAID
        msg.paid_at = timezone.now()
        if payment_intent:
            msg.stripe_payment_intent = payment_intent
        msg.save(update_fields=["status", "paid_at", "stripe_payment_intent"])
        transaction.on_commit(lambda: send_sms_task.delay(str(msg.id)))
    audit("payment_confirmed", msg.id)
    return True


@shared_task(bind=True, max_retries=3)
def send_sms_task(self, message_id: str):
    with transaction.atomic():
        msg = Message.objects.select_for_update().get(pk=message_id)
        if msg.status != Message.Status.PAID:
            return "skipped"  # already handled: webhooks and retries can repeat
        msg.status = Message.Status.QUEUED
        msg.save(update_fields=["status"])

    from .models import Blocklist

    if Blocklist.objects.filter(to_hash=msg.to_hash).exists():
        _fail(msg, "recipient_blocked", cancelled=True)
        return "blocked"

    try:
        to = decrypt(msg.to_enc)
        text = build_sms_text(decrypt(msg.body_enc), msg.optout_token)
        sid = send_sms(to, text)
    except SmsError as exc:
        if exc.permanent or self.request.retries >= self.max_retries:
            _fail(msg, exc.code or "send_failed")
            return "failed"
        Message.objects.filter(pk=msg.pk).update(status=Message.Status.PAID)
        raise self.retry(exc=exc, countdown=5 * 2 ** self.request.retries)
    except Exception:
        log.exception("unexpected send error for %s", msg.id)
        _fail(msg, "internal_error")
        return "failed"

    now = timezone.now()
    fields = {"provider_sid": sid, "status": Message.Status.SENT, "sent_at": now}
    if settings.SMS_PROVIDER == "console":  # demo mode has no delivery callback
        fields.update(status=Message.Status.DELIVERED, delivered_at=now)
    Message.objects.filter(pk=msg.pk).update(**fields)
    audit("message_sent", msg.id, provider=settings.SMS_PROVIDER)
    return "sent"


def _fail(msg: Message, code: str, cancelled: bool = False):
    status = Message.Status.CANCELLED if cancelled else Message.Status.UNDELIVERED
    Message.objects.filter(pk=msg.pk).update(status=status, error_code=code)
    msg.refresh_from_db()
    if settings.REFUND_ON_FAILURE:
        payments.refund(msg)
    audit("message_failed", msg.id, code=code)


@shared_task
def purge_expired() -> dict:
    """Wipe encrypted content after the TTL and delete old metadata."""
    now = timezone.now()
    unpaid = Message.objects.filter(
        status=Message.Status.AWAITING_PAYMENT, created_at__lte=now - timedelta(hours=2)
    ).update(status=Message.Status.EXPIRED)
    wiped = Message.objects.filter(expires_at__lte=now, purged_at__isnull=True).update(
        to_enc="", body_enc="", purged_at=now
    )
    cutoff = now - timedelta(days=settings.RETENTION_DAYS)
    deleted, _ = Message.objects.filter(created_at__lte=cutoff, reports__isnull=True).delete()
    return {"expired_unpaid": unpaid, "wiped": wiped, "deleted": deleted}
