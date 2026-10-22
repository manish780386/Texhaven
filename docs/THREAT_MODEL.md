# Threat model

| Threat | Mitigation | Where |
|---|---|---|
| Spam and harassment through the service | Payment before send, per-recipient and per-IP daily limits, scam/abuse scanner, hard-block on threats | `messaging/services.py`, `scanner/` |
| Phishing sent through Texhaven | Rules + URL analysis + Safe Browsing + AI layer; unsafe messages rejected and not stored | `scanner/engine.py` |
| Automated abuse (bots) | Cloudflare Turnstile (fails closed), DRF throttles per scope | `core/turnstile.py`, settings |
| Rate-limit evasion via spoofed `X-Forwarded-For` | Only trusts exactly `NUM_PROXIES` proxies | `core/net.py` |
| Recipient harassed repeatedly | Footer link to block or report, STOP keyword, block list by hashed number | `views.py` (Recipient*) |
| Database leak | Number and text encrypted (Fernet, key rotation); lookups by HMAC; wiped after 48 h | `core/crypto.py`, `tasks.purge_expired` |
| Forged payment or delivery callbacks | Stripe signature + timestamp check; Twilio signature check; idempotent state changes | webhooks in `views.py` |
| Double sending (webhook retries) | Row lock + status check in `mark_paid` and `send_sms_task` | `tasks.py` |
| Enumeration of recipients, signups | Generic errors, same response for duplicate waitlist emails, 24-char random tokens | `views.py` |
| Sender tracking link leak | Separate recipient token vs sender track id; tracking never shows text or full number | `models.Message` |
| Admin misuse | Encrypted fields hidden in admin; decrypt only via audited command; configurable admin URL | `admin.py`, `reveal_message` |
| Demo providers left on in production | App refuses to start unless Twilio + Stripe + keys are configured | `config/settings.py` |
| Prompt injection against the AI layer | Message treated as untrusted data, strict JSON parse, output clamped, fails open to rules | `scanner/llm.py` |
| Dependency vulnerabilities | CI runs `pip-audit` and `npm audit` | `.github/workflows/ci.yml` |

## Known limits
- The scanner is heuristic. It will miss novel scams and may flag some legitimate messages.
- Anyone who has the sender tracking link can see delivery status (not content).
- Hashing phone numbers with a secret pepper protects against casual leaks, not against someone who holds both DB and pepper.
- Compliance (A2P 10DLC, TCPA, GDPR, local telecom rules) is your responsibility before public launch.
