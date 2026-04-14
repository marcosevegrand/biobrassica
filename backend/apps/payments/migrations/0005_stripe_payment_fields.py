from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_payment_identifier_constraints'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='stripe_payment_intent_id',
            field=models.CharField(blank=True, db_index=True, max_length=255, verbose_name='ID do Payment Intent Stripe'),
        ),
        migrations.AddField(
            model_name='payment',
            name='stripe_session_id',
            field=models.CharField(blank=True, db_index=True, max_length=255, verbose_name='ID da sessão Stripe'),
        ),
        migrations.AddField(
            model_name='paymentcallback',
            name='provider_event_id',
            field=models.CharField(blank=True, db_index=True, max_length=255, verbose_name='ID do evento do provedor'),
        ),
        migrations.AddConstraint(
            model_name='payment',
            constraint=models.UniqueConstraint(
                condition=~Q(stripe_session_id=''),
                fields=('stripe_session_id',),
                name='payments_unique_stripe_session_id',
            ),
        ),
        migrations.AddConstraint(
            model_name='payment',
            constraint=models.UniqueConstraint(
                condition=~Q(stripe_payment_intent_id=''),
                fields=('stripe_payment_intent_id',),
                name='payments_unique_stripe_payment_intent_id',
            ),
        ),
        migrations.AddConstraint(
            model_name='paymentcallback',
            constraint=models.UniqueConstraint(
                condition=~Q(provider_event_id=''),
                fields=('provider_event_id',),
                name='payments_unique_provider_event_id',
            ),
        ),
    ]