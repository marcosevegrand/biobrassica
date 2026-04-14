from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_stripe_payment_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='method',
            field=models.CharField(
                choices=[
                    ('stripe', 'Stripe'),
                    ('multibanco', 'Multibanco'),
                    ('mbway', 'MB WAY'),
                    ('credit_card', 'Cartão de Crédito'),
                ],
                max_length=20,
                verbose_name='método',
            ),
        ),
    ]