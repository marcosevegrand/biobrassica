from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0009_provider_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='method',
            field=models.CharField(
                choices=[
                    ('stripe', 'Stripe'),
                    ('ifthenpay_mbway', 'Ifthenpay MB WAY'),
                ],
                max_length=20,
                verbose_name='método',
            ),
        ),
    ]