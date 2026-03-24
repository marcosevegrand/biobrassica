from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.payments.models import PaymentCallback


class Command(BaseCommand):
    help = 'Delete old payment callbacks according to the configured retention period.'

    def handle(self, *args, **options):
        retention_days = max(settings.PAYMENT_CALLBACK_RETENTION_DAYS, 1)
        threshold = timezone.now() - timedelta(days=retention_days)
        deleted_count, _ = PaymentCallback.objects.filter(created_at__lt=threshold).delete()
        self.stdout.write(
            self.style.SUCCESS(f'Removed {deleted_count} payment callbacks older than {retention_days} days.')
        )