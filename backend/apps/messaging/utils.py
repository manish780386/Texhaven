"""SMS length math, phone validation and footer helpers."""
import math
import re
from dataclasses import dataclass

import phonenumbers
from django.conf import settings
from phonenumbers import PhoneNumberType as T

GSM7_BASIC = (
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
)
GSM7_EXT = "^{}\\[~]|€"
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
TOKEN_LEN = 24
ALLOWED_TYPES = {T.MOBILE, T.FIXED_LINE_OR_MOBILE, T.VOIP}


@dataclass
class SmsInfo:
    encoding: str
    units: int
    segments: int


def sms_info(text: str) -> SmsInfo:
    """Mirror of frontend/src/lib/sms.ts. GSM-7 = 160/153 per segment, UCS-2 = 70/67."""
    if all(c in GSM7_BASIC or c in GSM7_EXT for c in text):
        units = sum(2 if c in GSM7_EXT else 1 for c in text)
        segs = 1 if units <= 160 else math.ceil(units / 153)
        return SmsInfo("gsm7", units, max(segs, 1) if units else 0)
    units = len(text.encode("utf-16-le")) // 2
    segs = 1 if units <= 70 else math.ceil(units / 67)
    return SmsInfo("ucs2", units, segs)


def footer_template() -> str:
    return settings.SMS_FOOTER_TEMPLATE


def build_sms_text(body: str, optout_token: str) -> str:
    return body + footer_template().replace("{token}", optout_token)


def clean_body(body: str) -> str:
    body = body.replace("\r\n", "\n").strip()
    return _CONTROL.sub("", body)


class NumberError(ValueError):
    pass


def normalize_number(raw: str):
    """Return (e164, region, masked). Raises NumberError with a user-safe message."""
    try:
        num = phonenumbers.parse(raw.strip(), None)
    except phonenumbers.NumberParseException:
        raise NumberError("Enter the number in international format, e.g. +14155550123.")
    if not phonenumbers.is_valid_number(num):
        raise NumberError("That does not look like a valid phone number.")
    if phonenumbers.number_type(num) not in ALLOWED_TYPES:
        raise NumberError("That number cannot receive text messages.")
    e164 = phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
    region = phonenumbers.region_code_for_number(num) or ""
    national = str(num.national_number)
    masked = f"+{num.country_code} " + "\u2022" * max(len(national) - 2, 0) + national[-2:]
    return e164, region, masked


def price_for(segments: int) -> int:
    return segments * settings.PRICE_PER_SEGMENT_CENTS


def mask_for_log(e164: str) -> str:
    return e164[:3] + "***" + e164[-2:]
