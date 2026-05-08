import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.orders.models import Order
from apps.orders.services import cancel_order_for_expired_payment
from apps.payments.models import Payment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cancel payments that have exceeded their expiration time.'

    def handle(self, *args, **options):
        now = timezone.now()
        expired_payments = Payment.objects.filter(
            status=Payment.Status.PENDING,
            expires_at__isnull=False,
            expires_at__lte=now,
        ).select_related('order')

        count = 0
        for payment in expired_payments:
            try:
                order = payment.order
                if order.status in {Order.Status.CANCELLED, Order.Status.DELIVERED}:
                    continue

                cancel_order_for_expired_payment(order)
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Cancelled payment #{payment.pk} (order #{order.pk})'))
            except Exception:
                logger.exception('Failed to cancel payment %s for order %s', payment.pk, payment.order_id)

        self.stdout.write(self.style.SUCCESS(f'Done. Cancelled {count} payment(s).'))
