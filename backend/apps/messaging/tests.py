import hashlib
import hmac
import json
import time
from datetime import timedelta
from urllib.parse import urlencode

from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.crypto import decrypt, hash_value

from .models import AbuseReport, AuditLog, Blocklist, Message, WaitlistEntry
from .tasks import purge_expired
from .utils import NumberError, normalize_number, sms_info

NUMBER = "+14155552671"
OK_BODY = "Hi! Running 10 minutes late, see you at the cafe."


class SmsMathTests(SimpleTestCase):
    def test_gsm7_segments(self):
        self.assertEqual(sms_info("a" * 160).segments, 1)
        self.assertEqual(sms_info("a" * 161).segments, 2)
        self.assertEqual(sms_info("a" * 306).segments, 2)
        self.assertEqual(sms_info("a" * 307).segments, 3)

    def test_extension_chars_count_double(self):
        self.assertEqual(sms_info("{" * 80).units, 160)
        self.assertEqual(sms_info("{" * 81).segments, 2)

    def test_unicode_switches_to_ucs2(self):
        info = sms_info("नमस्ते " * 5)
        self.assertEqual(info.encoding, "ucs2")
        self.assertEqual(sms_info("😀" * 35).segments, 1)  # 70 units
        self.assertEqual(sms_info("😀" * 36).segments, 2)

    def test_number_validation(self):
        self.assertEqual(normalize_number(NUMBER)[0], NUMBER)
        self.assertEqual(normalize_number("+91 98765 43210")[1], "IN")
        for bad in ("12345", "+1999", "hello"):
            with self.assertRaises(NumberError):
                normalize_number(bad)


class FlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.c = APIClient()

    def create(self, body=OK_BODY, to=NUMBER):
        return self.c.post("/api/v1/messages/", {"to": to, "body": body}, format="json")

    def test_full_happy_path(self):
        r = self.create()
        self.assertEqual(r.status_code, 201, r.content)
        data = r.json()
        self.assertEqual(data["status"], "awaiting_payment")
        self.assertIn("/mock-pay/", data["checkout_url"])
        self.assertNotIn(NUMBER, json.dumps(data))
        self.assertEqual(data["price_cents"], data["segments"] * 149)

        msg = Message.objects.get(track_id=data["id"])
        self.assertNotIn("4155552671", msg.to_enc)  # encrypted at rest
        self.assertEqual(decrypt(msg.body_enc), OK_BODY)

        with self.captureOnCommitCallbacks(execute=True):
            paid = self.c.post(f"/api/v1/messages/{data['id']}/mock-pay/")
        self.assertEqual(paid.status_code, 200)
        track = self.c.get(f"/api/v1/messages/{data['id']}/").json()
        self.assertEqual(track["status"], "delivered")
        self.assertNotIn("body", track)

    def test_payment_is_idempotent(self):
        data = self.create().json()
        with self.captureOnCommitCallbacks(execute=True):
            self.c.post(f"/api/v1/messages/{data['id']}/mock-pay/")
        with self.captureOnCommitCallbacks(execute=True):
            self.c.post(f"/api/v1/messages/{data['id']}/mock-pay/")
        self.assertEqual(AuditLog.objects.filter(event="message_sent").count(), 1)

    def test_unsafe_message_rejected_and_not_stored(self):
        r = self.create("Your bank account is suspended. Verify KYC now at http://hdfc-login.xyz and share the OTP")
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["code"], "unsafe")
        self.assertEqual(Message.objects.count(), 0)
        self.assertTrue(AuditLog.objects.filter(event="message_rejected").exists())

    def test_threat_rejected(self):
        self.assertEqual(self.create("I will find you and hurt you").status_code, 422)

    def test_bad_number(self):
        self.assertEqual(self.create(to="12345").status_code, 400)

    def test_unknown_track_id_404(self):
        self.assertEqual(self.c.get("/api/v1/messages/nope/").status_code, 404)

    def test_per_recipient_daily_limit(self):
        self.assertEqual(self.create().status_code, 201)
        self.assertEqual(self.create().status_code, 201)
        r = self.create()
        self.assertEqual(r.status_code, 429)
        self.assertEqual(r.json()["code"], "recipient_limit")

    def test_blocklisted_recipient_gets_generic_error(self):
        Blocklist.objects.create(to_hash=hash_value(NUMBER), source="admin")
        r = self.create()
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["code"], "recipient_unavailable")

    @override_settings(BLOCKED_COUNTRIES=["US"])
    def test_blocked_country(self):
        self.assertEqual(self.create().json()["code"], "country_blocked")

    def test_too_long(self):
        self.assertEqual(self.create("hello world " * 70).status_code, 400)

    @override_settings(PAYMENT_PROVIDER="stripe")
    def test_mock_pay_disabled_when_stripe(self):
        data_msg = Message.objects.create(
            track_id="t" * 24, optout_token="o" * 24, to_hash="h", to_masked="m", to_country="US",
            segments=1, encoding="gsm7", price_cents=149, currency="usd", sender_ip_hash="i",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.assertEqual(self.c.post(f"/api/v1/messages/{data_msg.track_id}/mock-pay/").status_code, 404)


class RecipientTests(TestCase):
    def setUp(self):
        cache.clear()
        self.c = APIClient()
        data = self.c.post("/api/v1/messages/", {"to": NUMBER, "body": OK_BODY}, format="json").json()
        self.msg = Message.objects.get(track_id=data["id"])

    def test_block_cancels_pending_and_blocks_future(self):
        r = self.c.post(f"/api/v1/recipient/{self.msg.optout_token}/block/")
        self.assertEqual(r.status_code, 200)
        self.msg.refresh_from_db()
        self.assertEqual(self.msg.status, "cancelled")
        self.assertTrue(Blocklist.objects.filter(to_hash=hash_value(NUMBER)).exists())
        again = self.c.post("/api/v1/messages/", {"to": NUMBER, "body": OK_BODY}, format="json")
        self.assertEqual(again.json()["code"], "recipient_unavailable")

    def test_report_creates_record_and_blocks(self):
        r = self.c.post(f"/api/v1/recipient/{self.msg.optout_token}/report/", {"category": "scam", "details": "fake"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(AbuseReport.objects.count(), 1)
        self.assertTrue(Blocklist.objects.exists())

    def test_sender_track_id_cannot_block(self):
        self.assertEqual(self.c.post(f"/api/v1/recipient/{self.msg.track_id}/block/").status_code, 404)


class WebhookTests(TestCase):
    def setUp(self):
        cache.clear()
        self.c = APIClient()

    def test_stripe_signature_required_and_marks_paid(self):
        data = self.c.post("/api/v1/messages/", {"to": NUMBER, "body": OK_BODY}, format="json").json()
        msg = Message.objects.get(track_id=data["id"])
        payload = json.dumps({
            "id": "evt_1", "object": "event", "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_1", "payment_status": "paid", "payment_intent": "pi_1",
                                 "metadata": {"message_id": str(msg.id)}}},
        })
        with override_settings(STRIPE_WEBHOOK_SECRET="whsec_test"):
            bad = self.c.post("/api/v1/webhooks/stripe/", payload, content_type="application/json", HTTP_STRIPE_SIGNATURE="t=1,v1=bad")
            self.assertEqual(bad.status_code, 400)
            ts = str(int(time.time()))
            sig = hmac.new(b"whsec_test", f"{ts}.{payload}".encode(), hashlib.sha256).hexdigest()
            with self.captureOnCommitCallbacks(execute=True):
                ok = self.c.post("/api/v1/webhooks/stripe/", payload, content_type="application/json", HTTP_STRIPE_SIGNATURE=f"t={ts},v1={sig}")
        self.assertEqual(ok.status_code, 200, ok.content)
        msg.refresh_from_db()
        self.assertEqual(msg.status, "delivered")
        self.assertEqual(msg.stripe_payment_intent, "pi_1")

    def test_twilio_stop_reply_blocks_number(self):
        r = self.c.post("/api/v1/webhooks/twilio/inbound/", urlencode({"From": NUMBER, "Body": " stop "}), content_type="application/x-www-form-urlencoded")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(Blocklist.objects.filter(to_hash=hash_value(NUMBER), source="stop_reply").exists())

    @override_settings(TWILIO_AUTH_TOKEN="secret", TURNSTILE_BYPASS=False)
    def test_twilio_unsigned_webhook_rejected(self):
        r = self.c.post("/api/v1/webhooks/twilio/inbound/", urlencode({"From": NUMBER, "Body": "STOP"}), content_type="application/x-www-form-urlencoded")
        self.assertEqual(r.status_code, 403)
        self.assertFalse(Blocklist.objects.exists())


class WaitlistAndPurgeTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_waitlist_is_idempotent(self):
        c = APIClient()
        for _ in range(2):
            self.assertEqual(c.post("/api/v1/waitlist/", {"email": "A@Example.com"}, format="json").status_code, 201)
        self.assertEqual(WaitlistEntry.objects.count(), 1)
        self.assertEqual(WaitlistEntry.objects.get().email, "a@example.com")
        self.assertEqual(c.post("/api/v1/waitlist/", {"email": "nope"}, format="json").status_code, 400)

    def test_purge_wipes_content(self):
        c = APIClient()
        data = c.post("/api/v1/messages/", {"to": NUMBER, "body": OK_BODY}, format="json").json()
        Message.objects.filter(track_id=data["id"]).update(expires_at=timezone.now() - timedelta(minutes=1))
        out = purge_expired()
        self.assertEqual(out["wiped"], 1)
        msg = Message.objects.get(track_id=data["id"])
        self.assertEqual((msg.to_enc, msg.body_enc), ("", ""))
        self.assertIsNotNone(msg.purged_at)
        self.assertTrue(c.get(f"/api/v1/messages/{data['id']}/").json()["content_deleted"])
