from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0009_websitecontent_payments_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='websitecontent',
            name='manual_mbway_number',
            field=models.CharField(
                blank=True,
                help_text='Usado quando PAYMENT_PROVIDER=mbway_manual para mostrar instruções de pagamento ao cliente.',
                max_length=20,
                verbose_name='número MB WAY manual',
            ),
        ),
    ]