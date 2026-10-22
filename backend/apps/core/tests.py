from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from apps.core import crypto, ratelimit


class CryptoTests(SimpleTestCase):
    def test_roundtrip_and_not_plaintext(self):
        token = crypto.encrypt("+14155552671")
        self.assertNotIn("4155552671", token)
        self.assertEqual(crypto.decrypt(token), "+14155552671")

    def test_hash_is_deterministic_and_keyed(self):
        self.assertEqual(crypto.hash_value("a"), crypto.hash_value("a"))
        self.assertNotEqual(crypto.hash_value("a"), crypto.hash_value("b"))
        before = crypto.hash_value("a")
        with override_settings(HASH_PEPPER="another-pepper"):
            self.assertNotEqual(before, crypto.hash_value("a"))

    def test_tokens_are_24_chars_and_unique(self):
        tokens = {crypto.new_token() for _ in range(50)}
        self.assertEqual(len(tokens), 50)
        self.assertTrue(all(len(t) == 24 for t in tokens))


class RateLimitTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_limit_enforced(self):
        results = [ratelimit.hit("k", 3, 60) for _ in range(5)]
        self.assertEqual(results, [True, True, True, False, False])


class PublicEndpointTests(TestCase):
    def test_health_and_config(self):
        c = APIClient()
        self.assertEqual(c.get("/api/v1/health/").status_code, 200)
        cfg = c.get("/api/v1/config/").json()
        self.assertIn("{token}", cfg["footer_template"])
        self.assertNotIn("secret", str(cfg).lower())

    def test_api_security_headers(self):
        r = APIClient().get("/api/v1/health/")
        self.assertEqual(r["Cache-Control"], "no-store")
        self.assertIn("default-src 'none'", r["Content-Security-Policy"])
