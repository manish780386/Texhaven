import uuid

from django.db import models
from django.utils import timezone


class Message(models.Model):
    class Status(models.TextChoices):
        AWAITING_PAYMENT = "awaiting_payment"
        PAID = "paid"
        QUEUED = "queued"
        SENT = "sent"
        DELIVERED = "delivered"
        UNDELIVERED = "undelivered"
        CANCELLED = "cancelled"
        EXPIRED = "expired"

    FINAL = {Status.DELIVERED, Status.UNDELIVERED, Status.CANCELLED, Status.EXPIRED}

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    track_id = models.CharField(max_length=32, unique=True)  # held by the sender
    optout_token = models.CharField(max_length=32, unique=True)  # held by the recipient (in the SMS footer)

    # Recipient number and body are encrypted at rest and wiped after MESSAGE_TTL_HOURS.
    to_enc = models.TextField(blank=True)
    body_enc = models.TextField(blank=True)
    to_hash = models.CharField(max_length=64, db_index=True)
    to_masked = models.CharField(max_length=32)
    to_country = models.CharField(max_length=2)

    segments = models.PositiveSmallIntegerField()
    encoding = models.CharField(max_length=8)
    price_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AWAITING_PAYMENT, db_index=True)
    risk_score = models.PositiveSmallIntegerField(default=0)
    risk_categories = models.JSONField(default=list, blank=True)
    sender_ip_hash = models.CharField(max_length=64, db_index=True)

    stripe_session_id = models.CharField(max_length=255, blank=True, db_index=True)
    stripe_payment_intent = models.CharField(max_length=255, blank=True)
    refunded = models.BooleanField(default=False)
    provider_sid = models.CharField(max_length=64, blank=True, db_index=True)
    error_code = models.CharField(max_length=32, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    paid_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True)
    purged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.track_id} [{self.status}]"


class Blocklist(models.Model):
    class Source(models.TextChoices):
        WEB = "web"
        STOP_REPLY = "stop_reply"
        ADMIN = "admin"

    to_hash = models.CharField(max_length=64, unique=True)
    source = models.CharField(max_length=12, choices=Source.choices)
    created_at = models.DateTimeField(default=timezone.now)


class AbuseReport(models.Model):
    class Category(models.TextChoices):
        SPAM = "spam"
        SCAM = "scam"
        HARASSMENT = "harassment"
        THREAT = "threat"
        OTHER = "other"

    message = models.ForeignKey(Message, null=True, on_delete=models.SET_NULL, related_name="reports")
    category = models.CharField(max_length=12, choices=Category.choices)
    details = models.CharField(max_length=500, blank=True)
    reporter_ip_hash = models.CharField(max_length=64)
    reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]


class AuditLog(models.Model):
    """Security events. Never contains phone numbers, message text or raw IPs."""

    event = models.CharField(max_length=40, db_index=True)
    message_id = models.UUIDField(null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class WaitlistEntry(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)
