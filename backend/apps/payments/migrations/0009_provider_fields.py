from django.db import migrations, models
from django.db.models import Q


def copy_stripe_identifiers_to_provider_fields(apps, schema_editor):
    Payment = apps.get_model('payments', 'Payment')
    Payment.objects.filter(method='stripe').update(
        provider_reference=models.F('stripe_session_id'),
        provider_payment_id=models.F('stripe_payment_intent_id'),
    )


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0008_alter_payment_checkout_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='provider_reference',
            field=models.CharField(blank=True, db_index=True, max_length=255, verbose_name='referência do provedor'),
        ),
        migrations.AddField(
            model_name='payment',
            name='provider_payment_id',
            field=models.CharField(blank=True, db_index=True, max_length=255, verbose_name='ID do pagamento no provedor'),
        ),
        migrations.AddField(
            model_name='payment',
            name='provider_data',
            field=models.JSONField(blank=True, default=dict, verbose_name='dados do provedor'),
        ),
        migrations.RunPython(copy_stripe_identifiers_to_provider_fields, noop_reverse),
        migrations.RemoveConstraint(
            model_name='payment',
            name='payments_unique_stripe_session_id',
        ),
        migrations.RemoveConstraint(
            model_name='payment',
            name='payments_unique_stripe_payment_intent_id',
        ),
        migrations.AddConstraint(
            model_name='payment',
            constraint=models.UniqueConstraint(
                condition=~Q(provider_reference=''),
                fields=('method', 'provider_reference'),
                name='payments_unique_provider_reference',
            ),
        ),
        migrations.AddConstraint(
            model_name='payment',
            constraint=models.UniqueConstraint(
                condition=~Q(provider_payment_id=''),
                fields=('method', 'provider_payment_id'),
                name='payments_unique_provider_payment_id',
            ),
        ),
        migrations.RemoveField(
            model_name='payment',
            name='stripe_session_id',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='stripe_payment_intent_id',
        ),
    ]