"""Texhaven settings. Everything sensitive comes from environment variables."""
import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name, default=""):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    return str(os.environ.get(name, str(default))).strip().lower() in ("1", "true", "yes", "on")


def env_int(name, default):
    return int(os.environ.get(name, default))


def env_list(name, default=""):
    return [x.strip() for x in os.environ.get(name, default).split(",") if x.strip()]


DEBUG = env_bool("DEBUG", False)

SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-insecure-secret-key-change-me"
    else:
        raise ImproperlyConfigured("SECRET_KEY is required when DEBUG is off.")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
FRONTEND_URL = env("FRONTEND_URL", "http://localhost:5173").rstrip("/")
PUBLIC_API_URL = env("PUBLIC_API_URL", "http://localhost:8000").rstrip("/")
ADMIN_URL = env("ADMIN_URL", "admin").strip("/")
ENABLE_API_DOCS = env_bool("ENABLE_API_DOCS", DEBUG)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "apps.core",
    "apps.scanner",
    "apps.messaging",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

# An empty DATABASE_URL (as in .env.example) falls back to local SQLite.
DATABASES = {
    "default": dj_database_url.parse(
        env("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=600
    )
}

REDIS_URL = env("REDIS_URL")
if REDIS_URL:
    CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": REDIS_URL}
    }
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# ---------------------------------------------------------------- API
# Number of reverse proxies in front of Django. 0 = trust only REMOTE_ADDR.
# Never trust X-Forwarded-For blindly: attackers can spoof it to dodge rate limits.
NUM_PROXIES = env_int("NUM_PROXIES", 0)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],  # anonymous, stateless API: no cookies, so no CSRF surface
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "config": "300/hour",
        "waitlist": "10/hour",
        "scan": "40/hour",
        "message_create": "15/hour",
        "track": "600/hour",
        "recipient": "60/hour",
    },
    "NUM_PROXIES": NUM_PROXIES,
    "UNAUTHENTICATED_USER": None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Texhaven API",
    "DESCRIPTION": "Send SMS from the browser with built-in scam and abuse protection.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", FRONTEND_URL)
CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS"]
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")

# ---------------------------------------------------------------- Security
if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "no-referrer"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# Keys. In production these are mandatory and must be unique random values.
# Generate with: python manage.py gen_keys
DATA_ENCRYPTION_KEYS = env_list("DATA_ENCRYPTION_KEYS")  # first key encrypts, all keys decrypt (rotation)
HASH_PEPPER = env("HASH_PEPPER")
if not DEBUG:
    for _name, _val in (("DATA_ENCRYPTION_KEYS", DATA_ENCRYPTION_KEYS), ("HASH_PEPPER", HASH_PEPPER)):
        if not _val:
            raise ImproperlyConfigured(f"{_name} is required when DEBUG is off. Run: python manage.py gen_keys")

# Bot protection (Cloudflare Turnstile). Bypass is only possible when DEBUG was on at startup.
TURNSTILE_SECRET_KEY = env("TURNSTILE_SECRET_KEY")
TURNSTILE_SITE_KEY = env("TURNSTILE_SITE_KEY")
TURNSTILE_BYPASS = env_bool("TURNSTILE_BYPASS", DEBUG) and DEBUG
if not DEBUG and not TURNSTILE_SECRET_KEY:
    raise ImproperlyConfigured("TURNSTILE_SECRET_KEY is required when DEBUG is off.")

# ---------------------------------------------------------------- Product
SMS_ENABLED = env_bool("SMS_ENABLED", True)
SMS_PROVIDER = env("SMS_PROVIDER", "console")  # console | twilio
PAYMENT_PROVIDER = env("PAYMENT_PROVIDER", "mock")  # mock | stripe
if SMS_ENABLED and not DEBUG:
    if SMS_PROVIDER != "twilio":
        raise ImproperlyConfigured("SMS_PROVIDER must be 'twilio' in production.")
    if PAYMENT_PROVIDER != "stripe":
        raise ImproperlyConfigured("PAYMENT_PROVIDER must be 'stripe' in production.")

TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = env("TWILIO_FROM_NUMBER")
TWILIO_MESSAGING_SERVICE_SID = env("TWILIO_MESSAGING_SERVICE_SID")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET")

PRICE_PER_SEGMENT_CENTS = env_int("PRICE_PER_SEGMENT_CENTS", 149)
CURRENCY = env("CURRENCY", "usd").lower()
MAX_SEGMENTS = env_int("MAX_SEGMENTS", 4)
MESSAGE_TTL_HOURS = env_int("MESSAGE_TTL_HOURS", 48)
RETENTION_DAYS = env_int("RETENTION_DAYS", 90)
REFUND_ON_FAILURE = env_bool("REFUND_ON_FAILURE", True)
BLOCKED_COUNTRIES = [c.upper() for c in env_list("BLOCKED_COUNTRIES")]
DAILY_LIMIT_PER_RECIPIENT = env_int("DAILY_LIMIT_PER_RECIPIENT", 2)
DAILY_LIMIT_PER_IP = env_int("DAILY_LIMIT_PER_IP", 5)
SMS_FOOTER_TEMPLATE = env(
    "SMS_FOOTER_TEMPLATE",
    "\n\n- Sent via Texhaven. Block or report: " + FRONTEND_URL + "/stop/{token}",
)

# Scanner
BLOCK_THRESHOLD = env_int("BLOCK_THRESHOLD", 60)
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = env("ANTHROPIC_MODEL", "claude-haiku-5-5")
GOOGLE_SAFE_BROWSING_API_KEY = env("GOOGLE_SAFE_BROWSING_API_KEY")

# ---------------------------------------------------------------- Celery
CELERY_BROKER_URL = REDIS_URL or "memory://"
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_EAGER", DEBUG)
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_TASK_ACKS_LATE = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BEAT_SCHEDULE = {
    "purge-expired-messages": {"task": "apps.messaging.tasks.purge_expired", "schedule": 900.0},
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}
