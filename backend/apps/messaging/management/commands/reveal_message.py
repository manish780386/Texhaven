from django.core.management.base import BaseCommand, CommandError

from apps.core.crypto import decrypt
from apps.messaging.models import Message
from apps.messaging.services import audit


class Command(BaseCommand):
    help = "Decrypt one message for a valid legal request. The access is written to the audit log."

    def add_arguments(self, parser):
        parser.add_argument("track_id")
        parser.add_argument("--reason", required=True, help="Case or request reference")

    def handle(self, *args, track_id, reason, **options):
        try:
            msg = Message.objects.get(track_id=track_id)
        except Message.DoesNotExist:
            raise CommandError("Message not found.")
        if not msg.body_enc:
            raise CommandError("Content was already deleted (retention policy).")
        audit("content_revealed", msg.id, reason=reason[:200])
        self.stdout.write(f"to:   {decrypt(msg.to_enc)}\nbody: {decrypt(msg.body_enc)}")
