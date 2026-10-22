<<<<<<< HEAD

Send SMS from any browser with built-in scam and abuse protection. No app, no account.

**Stack:** React 18 + TypeScript + Vite + Tailwind (frontend) / Django 5 + DRF + Celery (backend) /
Postgres, Redis / Twilio (SMS) / Stripe (payments) / Cloudflare Turnstile (bots) / Claude + Google Safe Browsing (optional scam layers).

```
frontend/   React app (landing, send, track, scam checker, recipient block/report)
backend/    Django API (messages, scanner, webhooks, admin, Celery tasks)
docs/       THREAT_MODEL.md
```

## Run locally (2 terminals, no accounts needed)

Demo mode uses a console SMS provider and a simulated payment page, so you can try everything for free.

```bash
# 1) backend
cd backend
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver                               # http://localhost:8000  (docs: /api/docs/)

# 2) frontend
cd frontend
npm install
npm run dev                                              # http://localhost:5173
```

In `backend/.env` the Turnstile keys are Cloudflare's public test keys. If the widget cannot load
(offline, ad blocker), set `TURNSTILE_SITE_KEY=` to empty: local dev then skips the widget.

Tests: `cd backend && DEBUG=True python manage.py test apps` (42 tests) and `cd frontend && npm test`.
Full stack with Postgres, Redis, worker and beat: `docker compose up --build` (needs `backend/.env`).

## How a message flows

1. Browser posts number + text + Turnstile token to `POST /api/v1/messages/`.
2. Backend validates the number (libphonenumber), checks the block list, applies rate limits, then scans the text.
   Unsafe text is rejected with reasons and is never stored.
3. A `Message` row is created (number and text **encrypted**, lookups use **HMAC hashes**) and a Stripe Checkout URL is returned.
4. Stripe webhook (signature verified) marks it paid, which queues a Celery task that sends via Twilio.
5. Twilio status webhook (signature verified) updates delivery; failures are auto-refunded.
6. The SMS ends with a link to `/stop/<token>` so the recipient can block the number or report abuse. Replying STOP also blocks.
7. A beat task wipes number and text after 48 hours.

## Scam scanner layers

`backend/apps/scanner/`: (1) 16 text rules combined with noisy-OR scoring, (2) URL analysis (look-alike brand domains,
IP hosts, shorteners, punycode, `@` tricks, bad TLDs), (3) Google Safe Browsing (optional key),
(4) Claude second opinion for borderline scores (optional key). Threats and harassment are hard-blocked.

## Go to production checklist

1. `python manage.py gen_keys` and put `SECRET_KEY`, `DATA_ENCRYPTION_KEYS`, `HASH_PEPPER` in your host's secret store.
2. Set `DEBUG=False`, `SMS_PROVIDER=twilio`, `PAYMENT_PROVIDER=stripe` (the app refuses to start with demo providers in production).
3. Real Turnstile keys, Postgres `DATABASE_URL`, Redis `REDIS_URL`, `ALLOWED_HOSTS`, `FRONTEND_URL`, `PUBLIC_API_URL`, `CORS_ALLOWED_ORIGINS`.
4. Set `NUM_PROXIES` to how many proxies sit in front of Django (otherwise rate limits see the proxy's IP).
5. Stripe: webhook endpoint `/api/v1/webhooks/stripe/` for `checkout.session.completed`.
   Twilio: status callback is set automatically; set the inbound webhook to `/api/v1/webhooks/twilio/inbound/`.
6. Twilio needs sender registration in many countries (for example A2P 10DLC in the US) and reviews acceptable use. Start with a few countries via `BLOCKED_COUNTRIES`.
7. Edit `frontend/public/_headers` (replace `YOUR-API-DOMAIN`) and have a lawyer review the Legal page.
8. Run the Celery worker and beat (`celery -A config worker`, `celery -A config beat`).

### Cheap hosting

Frontend: Cloudflare Pages or Vercel (`VITE_API_URL=https://api.yourdomain/api/v1`). Backend: Railway, Render or Fly.io.
Free backend tiers sleep when idle (30-50 s first request), so use a small paid plan before a BetaList launch.
Vercel Hobby is non-commercial; Cloudflare Pages is fine for a paid product.

## Useful commands

```bash
python manage.py gen_keys                       # generate secrets
python manage.py createsuperuser                # admin at /<ADMIN_URL>/
python manage.py reveal_message <track_id> --reason "case 123"   # decrypt for a legal request (audited)
```
=======
# Texhaven
>>>>>>> f6cd439d18b25f52bbcc65f830b43fb7a89c8bbe
