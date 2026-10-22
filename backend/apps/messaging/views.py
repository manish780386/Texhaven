import json
import logging

import stripe
from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from twilio.request_validator import RequestValidator

from apps.core import turnstile
from apps.core.crypto import hash_value
from apps.core.net import client_ip

from . import payments
from .models import AbuseReport, Blocklist, Message, WaitlistEntry
from .serializers import MessageCreateSerializer, ReportSerializer, WaitlistSerializer
from .services import Rejected, audit, block_number, create_message
from .tasks import mark_paid
from .utils import normalize_number, NumberError

log = logging.getLogger(__name__)


def bot_fail():
    return Response({"detail": "Bot check failed. Please retry."}, status=status.HTTP_400_BAD_REQUEST)


def not_found():
    return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)


def _public(msg: Message) -> dict:
    """What the sender can see. Never includes the text or the full number."""
    return {
        "id": msg.track_id,
        "status": msg.status,
        "to": msg.to_masked,
        "country": msg.to_country,
        "segments": msg.segments,
        "price_cents": msg.price_cents,
        "currency": msg.currency,
        "created_at": msg.created_at,
        "paid_at": msg.paid_at,
        "sent_at": msg.sent_at,
        "delivered_at": msg.delivered_at,
        "expires_at": msg.expires_at,
        "content_deleted": msg.purged_at is not None,
        "refunded": msg.refunded,
    }


class WaitlistView(APIView):
    throttle_scope = "waitlist"

    def post(self, request):
        ser = WaitlistSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if not turnstile.verify(ser.validated_data.get("turnstile_token"), client_ip(request)):
            return bot_fail()
        try:
            with transaction.atomic():
                WaitlistEntry.objects.create(email=ser.validated_data["email"].lower())
        except IntegrityError:
            pass  # duplicate: same response, so signups cannot be enumerated
        return Response({"ok": True}, status=status.HTTP_201_CREATED)


class MessageCreateView(APIView):
    throttle_scope = "message_create"

    def post(self, request):
        ser = MessageCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ip = client_ip(request)
        if not turnstile.verify(ser.validated_data.get("turnstile_token"), ip):
            return bot_fail()
        try:
            msg, checkout_url = create_message(raw_to=ser.validated_data["to"], body=ser.validated_data["body"], ip=ip)
        except Rejected as exc:
            return Response({"code": exc.code, "detail": exc.detail, **exc.extra}, status=exc.http_status)
        return Response({**_public(msg), "checkout_url": checkout_url}, status=status.HTTP_201_CREATED)


class MessageDetailView(APIView):
    throttle_scope = "track"

    def get(self, request, track_id):
        try:
            msg = Message.objects.get(track_id=track_id)
        except Message.DoesNotExist:
            return not_found()
        return Response(_public(msg))


class MockPayView(APIView):
    """Demo only: lets you try the full flow without Stripe. Disabled when PAYMENT_PROVIDER=stripe."""

    throttle_scope = "track"

    def post(self, request, track_id):
        if settings.PAYMENT_PROVIDER != "mock":
            return not_found()
        try:
            msg = Message.objects.get(track_id=track_id)
        except Message.DoesNotExist:
            return not_found()
        mark_paid(str(msg.id))
        msg.refresh_from_db()
        return Response(_public(msg))


# ----------------------------------------------------------- recipient safety (token comes from the SMS footer)
def _by_token(token):
    return Message.objects.filter(optout_token=token).first()


class RecipientView(APIView):
    throttle_scope = "recipient"

    def get(self, request, token):
        msg = _by_token(token)
        if not msg:
            return not_found()
        return Response({"to": msg.to_masked, "blocked": Blocklist.objects.filter(to_hash=msg.to_hash).exists()})


class RecipientBlockView(APIView):
    throttle_scope = "recipient"

    def post(self, request, token):
        msg = _by_token(token)
        if not msg:
            return not_found()
        block_number(msg.to_hash, "web")
        # Cancel anything still pending to this number and refund the senders.
        pending = Message.objects.filter(
            to_hash=msg.to_hash, status__in=[Message.Status.AWAITING_PAYMENT, Message.Status.PAID]
        )
        for m in pending:
            was_paid = m.status == Message.Status.PAID
            Message.objects.filter(pk=m.pk).update(status=Message.Status.CANCELLED, error_code="recipient_blocked")
            if was_paid:
                m.refresh_from_db()
                payments.refund(m)
        audit("recipient_blocked", msg.id, source="web")
        return Response({"blocked": True})


class RecipientReportView(APIView):
    throttle_scope = "recipient"

    def post(self, request, token):
        msg = _by_token(token)
        if not msg:
            return not_found()
        ser = ReportSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ip = client_ip(request)
        if not turnstile.verify(ser.validated_data.get("turnstile_token"), ip):
            return bot_fail()
        AbuseReport.objects.create(
            message=msg,
            category=ser.validated_data["category"],
            details=ser.validated_data.get("details", ""),
            reporter_ip_hash=hash_value(ip),
        )
        block_number(msg.to_hash, "web")  # reporting also stops further messages to this number
        audit("abuse_reported", msg.id, category=ser.validated_data["category"])
        return Response({"reported": True}, status=status.HTTP_201_CREATED)


# ----------------------------------------------------------- provider webhooks
class _Webhook(APIView):
    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes: list = []


class StripeWebhookView(_Webhook):
    def post(self, request):
        if not settings.STRIPE_WEBHOOK_SECRET:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            # Verifies the signature and timestamp (replay protection) before we trust anything.
            stripe.Webhook.construct_event(
                request.body, request.META.get("HTTP_STRIPE_SIGNATURE", ""), settings.STRIPE_WEBHOOK_SECRET
            )
            event = json.loads(request.body)
        except (ValueError, stripe.SignatureVerificationError):
            return Response({"detail": "Invalid signature."}, status=status.HTTP_400_BAD_REQUEST)

        if event["type"] in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
            session = event["data"]["object"]
            if session.get("payment_status") == "paid":
                message_id = (session.get("metadata") or {}).get("message_id") or session.get("client_reference_id")
                try:
                    mark_paid(message_id, session.get("payment_intent") or "")
                except (Message.DoesNotExist, ValueError):
                    log.warning("stripe event for unknown message")
        return Response({"received": True})


def _valid_twilio(request) -> bool:
    token = settings.TWILIO_AUTH_TOKEN
    if not token:
        return settings.TURNSTILE_BYPASS  # unsigned webhooks only in local development
    url = settings.PUBLIC_API_URL + request.get_full_path()
    signature = request.META.get("HTTP_X_TWILIO_SIGNATURE", "")
    return RequestValidator(token).validate(url, request.POST.dict(), signature)


_RANK = {"awaiting_payment": 0, "paid": 1, "queued": 2, "sent": 3, "delivered": 4, "undelivered": 4}
_TWILIO_MAP = {
    "accepted": "queued", "scheduled": "queued", "queued": "queued", "sending": "queued",
    "sent": "sent", "delivered": "delivered", "undelivered": "undelivered", "failed": "undelivered",
}


class TwilioStatusView(_Webhook):
    parser_classes = [FormParser]

    def post(self, request):
        if not _valid_twilio(request):
            return Response(status=status.HTTP_403_FORBIDDEN)
        sid, new = request.POST.get("MessageSid", ""), _TWILIO_MAP.get(request.POST.get("MessageStatus", ""))
        msg = Message.objects.filter(provider_sid=sid).first() if sid else None
        if msg and new and _RANK.get(new, 0) >= _RANK.get(msg.status, 0) and msg.status != Message.Status.DELIVERED:
            fields = {"status": new}
            if new == "delivered":
                fields["delivered_at"] = timezone.now()
            if new == "undelivered":
                fields["error_code"] = request.POST.get("ErrorCode", "")[:32]
            Message.objects.filter(pk=msg.pk).update(**fields)
            if new == "undelivered" and settings.REFUND_ON_FAILURE:
                msg.refresh_from_db()
                payments.refund(msg)
        return HttpResponse(status=204)


STOP_WORDS = {"STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"}


class TwilioInboundView(_Webhook):
    """Recipient replied to a Texhaven message. STOP keywords add the number to the blocklist."""

    parser_classes = [FormParser]

    def post(self, request):
        if not _valid_twilio(request):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if request.POST.get("Body", "").strip().upper() in STOP_WORDS:
            try:
                e164, _, _ = normalize_number(request.POST.get("From", ""))
            except NumberError:
                e164 = ""
            if e164:
                block_number(hash_value(e164), "stop_reply")
                audit("stop_reply")
        return HttpResponse("<Response></Response>", content_type="text/xml")
