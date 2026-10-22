import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import Message

log = logging.getLogger(__name__)


def create_checkout(message: Message) -> str:
    """Return a URL where the sender pays. 'mock' provider = local demo page, never in production."""
    if settings.PAYMENT_PROVIDER != "stripe":
        return f"{settings.FRONTEND_URL}/mock-pay/{message.track_id}"

    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "quantity": 1,
                "price_data": {
                    "currency": message.currency,
                    "unit_amount": message.price_cents,
                    "product_data": {"name": f"Texhaven SMS ({message.segments} segment{'s' if message.segments > 1 else ''})"},
                },
            }
        ],
        client_reference_id=str(message.id),
        metadata={"message_id": str(message.id)},
        success_url=f"{settings.FRONTEND_URL}/track/{message.track_id}?paid=1",
        cancel_url=f"{settings.FRONTEND_URL}/send?cancelled=1",
        expires_at=int((timezone.now() + timedelta(minutes=35)).timestamp()),
        idempotency_key=f"texhaven-checkout-{message.id}",
    )
    message.stripe_session_id = session.id
    message.save(update_fields=["stripe_session_id"])
    return session.url


def refund(message: Message) -> bool:
    """Refund a paid message once. Returns True when a refund was issued."""
    if message.refunded or not message.stripe_payment_intent or settings.PAYMENT_PROVIDER != "stripe":
        return False
    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        stripe.Refund.create(
            payment_intent=message.stripe_payment_intent,
            idempotency_key=f"texhaven-refund-{message.id}",
        )
    except Exception:
        log.exception("refund failed for message %s", message.id)
        return False
    message.refunded = True
    message.save(update_fields=["refunded"])
    return True
