from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_orderitem_quantity_limits'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pendente'),
                    ('payment_pending', 'Aguarda Pagamento'),
                    ('paid', 'Pago'),
                    ('preparing', 'Em Preparação'),
                    ('ready', 'Pronta'),
                    ('in_transit', 'Em Transporte'),
                    ('delivered', 'Entregue'),
                    ('cancelled', 'Cancelado'),
                ],
                default='pending',
                max_length=20,
                verbose_name='estado',
            ),
        ),
    ]
