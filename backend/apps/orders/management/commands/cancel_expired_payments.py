import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.orders.models import Order
from apps.orders.services import cancel_unpaid_order
from apps.payments.models import Payment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cancel orders with expired payments.'

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

                cancel_unpaid_order(order)
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Cancelled order #{order.pk} (payment #{payment.pk})'))
            except Exception:
                logger.exception('Failed to cancel order %s with expired payment %s', payment.order_id, payment.pk)

        self.stdout.write(self.style.SUCCESS(f'Done. Cancelled {count} order(s).'))
