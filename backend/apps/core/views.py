from django.conf import settings
from django.db import connection
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.messaging.utils import footer_template


class HealthView(APIView):
    throttle_classes: list = []

    def get(self, request):
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        return Response({"status": "ok"})


class ConfigView(APIView):
    """Public settings the frontend needs. Nothing secret here."""

    throttle_scope = "config"

    def get(self, request):
        return Response(
            {
                "sms_enabled": settings.SMS_ENABLED,
                "demo_mode": settings.PAYMENT_PROVIDER == "mock" or settings.SMS_PROVIDER == "console",
                "price_per_segment_cents": settings.PRICE_PER_SEGMENT_CENTS,
                "currency": settings.CURRENCY,
                "max_segments": settings.MAX_SEGMENTS,
                "ttl_hours": settings.MESSAGE_TTL_HOURS,
                "turnstile_site_key": settings.TURNSTILE_SITE_KEY,
                "footer_template": footer_template(),
                "blocked_countries": settings.BLOCKED_COUNTRIES,
            }
        )
