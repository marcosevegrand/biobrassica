from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0010_alter_payment_method'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='method',
            field=models.CharField(
                choices=[
                    ('stripe', 'Stripe'),
                    ('ifthenpay_mbway', 'Ifthenpay MB WAY'),
                    ('mbway_manual', 'MB WAY manual'),
                ],
                max_length=20,
                verbose_name='método',
            ),
        ),
    ]