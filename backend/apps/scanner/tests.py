from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from .engine import scan
from .urls_check import analyze, extract_urls

NO_NET = dict(use_ai=False, use_safe_browsing=False)


class EngineTests(SimpleTestCase):
    def test_benign_message_is_low(self):
        r = scan("Hey! Are we still on for lunch at 1? I will bring the notes.", **NO_NET)
        self.assertEqual(r.level, "low")
        self.assertEqual(r.reasons, [])

    def test_legit_brand_link_is_not_flagged(self):
        r = scan("Your Amazon order has shipped: https://www.amazon.com/orders", **NO_NET)
        self.assertEqual(r.level, "low")

    def test_kyc_phishing_is_high(self):
        r = scan("Dear customer your bank account will be suspended today. Verify KYC immediately at http://hdfc-secure-login.xyz/kyc", **NO_NET)
        self.assertEqual(r.level, "high")
        self.assertIn("credential_theft", r.categories)

    def test_otp_request(self):
        r = scan("This is your bank. Please share the OTP you received to verify your account urgently", **NO_NET)
        self.assertGreaterEqual(r.score, 60)

    def test_threat_is_hard_blocked(self):
        r = scan("I will find you and hurt you", **NO_NET)
        self.assertTrue(r.hard_block)
        self.assertEqual(r.level, "high")

    def test_zero_width_obfuscation_is_normalized(self):
        r = scan("I\u200b will k\u200bill you", **NO_NET)
        self.assertIn("threat", r.categories)

    def test_prize_scam(self):
        r = scan("Congratulations! You have won a lottery prize. Claim your reward now at bit.ly/abc123", **NO_NET)
        self.assertEqual(r.level, "high")

    def test_score_never_exceeds_100(self):
        text = "urgent verify your account suspended you won lottery pay fee gift card otp share http://1.2.3.4/x"
        self.assertLessEqual(scan(text, **NO_NET).score, 100)


class UrlTests(SimpleTestCase):
    def test_extract(self):
        self.assertEqual(extract_urls("see https://a.com/x, and bit.ly/zz."), ["https://a.com/x", "bit.ly/zz"])

    def test_email_is_not_url(self):
        self.assertEqual(extract_urls("mail me at john@example.com"), [])

    def test_lookalike_and_ip_and_userinfo(self):
        codes = lambda u: [s[0] for s in analyze(u)["signals"]]
        self.assertIn("url_brand_lookalike", codes("https://paypa1.com/login"))
        self.assertIn("url_ip_host", codes("http://192.168.1.5/login"))
        self.assertIn("url_userinfo", codes("https://google.com@evil.example/x"))
        self.assertNotIn("url_brand_lookalike", codes("https://www.paypal.com/signin"))


class ScanApiTests(TestCase):
    def test_scan_endpoint(self):
        r = APIClient().post("/api/v1/scan/", {"text": "Your parcel is held, pay customs fee at http://dhl-track.top/x"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["level"], "high")

    def test_scan_validation(self):
        self.assertEqual(APIClient().post("/api/v1/scan/", {"text": ""}, format="json").status_code, 400)
