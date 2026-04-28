from django.db import migrations, models


def drop_legacy_payment_methods(apps, schema_editor):
    Payment = apps.get_model('payments', 'Payment')
    # Migrate any legacy stripe/ifthenpay rows to manual MB WAY (will need to be
    # reviewed manually in the admin afterwards).
    Payment.objects.filter(method__in=['stripe', 'ifthenpay_mbway']).update(method='mbway_manual')


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0011_alter_payment_method'),
    ]

    operations = [
        migrations.RunPython(drop_legacy_payment_methods, noop_reverse),
        migrations.DeleteModel(name='PaymentCallback'),
        migrations.AlterField(
            model_name='payment',
            name='method',
            field=models.CharField(
                choices=[
                    ('mbway_manual', 'MB WAY'),
                    ('bank_transfer', 'Transferência bancária'),
                ],
                max_length=20,
                verbose_name='método',
            ),
        ),
    ]
