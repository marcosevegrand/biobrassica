from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_payment_checkout_url_and_callback_reason'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='payment',
            constraint=models.UniqueConstraint(
                condition=~Q(ifthenpay_request_id=''),
                fields=('ifthenpay_request_id',),
                name='payments_unique_ifthenpay_request_id',
            ),
        ),
        migrations.AddConstraint(
            model_name='payment',
            constraint=models.UniqueConstraint(
                condition=~Q(mb_entity='') & ~Q(mb_reference=''),
                fields=('mb_entity', 'mb_reference'),
                name='payments_unique_mb_entity_reference',
            ),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['status', 'expires_at'], name='payments_status_expires_idx'),
        ),
    ]