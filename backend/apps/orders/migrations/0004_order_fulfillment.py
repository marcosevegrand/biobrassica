from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_order_access_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='fulfillment_method',
            field=models.CharField(choices=[('pickup', 'Levantamento na loja'), ('shipping', 'Envio ao domicílio')], default='pickup', max_length=20, verbose_name='método de entrega'),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_address_line1',
            field=models.CharField(blank=True, max_length=255, verbose_name='morada'),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_address_line2',
            field=models.CharField(blank=True, max_length=255, verbose_name='morada (cont.)'),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_city',
            field=models.CharField(blank=True, max_length=100, verbose_name='cidade'),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_postal_code',
            field=models.CharField(blank=True, max_length=10, verbose_name='código postal'),
        ),
        migrations.AlterField(
            model_name='order',
            name='pickup_location',
            field=models.CharField(blank=True, choices=[('braga', 'Loja Braga'), ('guimaraes', 'Loja Guimarães')], max_length=20, verbose_name='local de levantamento'),
        ),
    ]