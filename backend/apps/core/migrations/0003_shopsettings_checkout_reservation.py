from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_shopsettings_payment_timeout_minutes'),
    ]

    operations = [
        migrations.AddField(
            model_name='shopsettings',
            name='checkout_reservation_minutes',
            field=models.PositiveIntegerField(
                default=30,
                help_text='Quanto tempo o stock fica reservado enquanto o cliente preenche o checkout. Após expirar, o stock é libertado e o cliente tem de recomeçar. Defina 0 para desativar.',
                verbose_name='tempo limite para reserva no checkout (minutos)',
            ),
        ),
        migrations.AlterField(
            model_name='shopsettings',
            name='payment_timeout_minutes',
            field=models.PositiveIntegerField(
                default=30,
                help_text='Após este tempo, o pagamento expirado é cancelado. A encomenda permanece pendente — o cliente pode reiniciar o pagamento. Defina 0 para desativar.',
                verbose_name='tempo limite para pagamento (minutos)',
            ),
        ),
    ]
