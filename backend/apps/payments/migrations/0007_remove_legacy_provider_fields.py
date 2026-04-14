from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0006_alter_payment_method'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='payment',
            name='payments_unique_ifthenpay_request_id',
        ),
        migrations.RemoveConstraint(
            model_name='payment',
            name='payments_unique_mb_entity_reference',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='ifthenpay_request_id',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='mb_entity',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='mb_reference',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='mbway_phone',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='mbway_transaction_id',
        ),
        migrations.AlterField(
            model_name='payment',
            name='method',
            field=models.CharField(choices=[('stripe', 'Stripe')], max_length=20, verbose_name='método'),
        ),
    ]
