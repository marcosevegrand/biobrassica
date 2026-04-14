from django.core.management.base import BaseCommand

from apps.payments.services import expire_stale_pending_payments


class Command(BaseCommand):
    help = 'Expire pending payments whose local checkout deadline has elapsed.'

    def handle(self, *args, **options):
        expired_count = expire_stale_pending_payments()
        self.stdout.write(
            self.style.SUCCESS(f'Expired {expired_count} stale pending payment(s).')
        )