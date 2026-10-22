"""SMS delivery providers. 'console' is for local demos only (blocked in production by settings)."""
import logging
import uuid

from django.conf import settings

from .utils import mask_for_log

log = logging.getLogger(__name__)


class SmsError(Exception):
    def __init__(self, message: str, permanent: bool, code: str = ""):
        super().__init__(message)
        self.permanent = permanent
        self.code = code


def send_sms(to: str, text: str) -> str:
    """Send one SMS and return the provider message id."""
    if settings.SMS_PROVIDER == "twilio":
        return _send_twilio(to, text)
    sid = f"console-{uuid.uuid4().hex[:12]}"
    log.info("[console sms] to=%s chars=%d sid=%s", mask_for_log(to), len(text), sid)
    return sid


def _send_twilio(to: str, text: str) -> str:
    from twilio.base.exceptions import TwilioException, TwilioRestException
    from twilio.rest import Client

    params = {
        "to": to,
        "body": text,
        "status_callback": f"{settings.PUBLIC_API_URL}/api/v1/webhooks/twilio/status/",
    }
    if settings.TWILIO_MESSAGING_SERVICE_SID:
        params["messaging_service_sid"] = settings.TWILIO_MESSAGING_SERVICE_SID
    else:
        params["from_"] = settings.TWILIO_FROM_NUMBER
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        return client.messages.create(**params).sid
    except TwilioRestException as exc:
        permanent = 400 <= (exc.status or 0) < 500 and exc.status != 429
        raise SmsError(str(exc.msg)[:200], permanent=permanent, code=str(exc.code or ""))
    except TwilioException as exc:
        raise SmsError(str(exc)[:200], permanent=False)
