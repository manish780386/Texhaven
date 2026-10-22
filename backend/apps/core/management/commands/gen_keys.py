import secrets

from cryptography.fernet import Fernet
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key


class Command(BaseCommand):
    help = "Generate SECRET_KEY, DATA_ENCRYPTION_KEYS and HASH_PEPPER values for your .env"

    def handle(self, *args, **options):
        self.stdout.write(f"SECRET_KEY={get_random_secret_key()}")
        self.stdout.write(f"DATA_ENCRYPTION_KEYS={Fernet.generate_key().decode()}")
        self.stdout.write(f"HASH_PEPPER={secrets.token_hex(32)}")
        self.stdout.write(self.style.WARNING("Store these in your secret manager. Never commit them."))
