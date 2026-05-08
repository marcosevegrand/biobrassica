import logging

from django.core.management.base import BaseCommand

from apps.cart.services import release_expired_reservations

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Release expired cart stock reservations.'

    def handle(self, *args, **options):
        released = release_expired_reservations()
        self.stdout.write(self.style.SUCCESS(f'Released {released} expired cart reservation(s).'))
