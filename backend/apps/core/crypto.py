"""Field encryption (Fernet, key rotation via MultiFernet) and keyed hashing."""
import base64
import hashlib
import hmac
import secrets

from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings


def _dev_key() -> bytes:
    return base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())


def _fernet() -> MultiFernet:
    keys = [k.encode() for k in settings.DATA_ENCRYPTION_KEYS] or [_dev_key()]
    return MultiFernet([Fernet(k) for k in keys])


def encrypt(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode("ascii")).decode("utf-8")


def hash_value(value: str) -> str:
    """Deterministic keyed hash (HMAC-SHA256). Used for blocklists and rate limits so we never
    need the raw phone number or IP address for lookups."""
    pepper = (settings.HASH_PEPPER or settings.SECRET_KEY).encode()
    return hmac.new(pepper, value.encode("utf-8"), hashlib.sha256).hexdigest()


def new_token(nbytes: int = 18) -> str:
    """URL-safe random token. 18 bytes -> exactly 24 characters."""
    return secrets.token_urlsafe(nbytes)
