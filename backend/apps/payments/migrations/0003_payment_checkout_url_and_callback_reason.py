from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_alter_payment_amount_alter_payment_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='ifthenpay_request_id',
            field=models.CharField(blank=True, db_index=True, max_length=255, verbose_name='ID do pedido Ifthenpay'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='mb_reference',
            field=models.CharField(blank=True, db_index=True, max_length=20, verbose_name='referência MB'),
        ),
        migrations.AddField(
            model_name='payment',
            name='checkout_url',
            field=models.URLField(blank=True, verbose_name='URL de checkout'),
        ),
        migrations.AddField(
            model_name='payment',
            name='last_error',
            field=models.TextField(blank=True, verbose_name='último erro'),
        ),
        migrations.AddField(
            model_name='paymentcallback',
            name='validation_message',
            field=models.CharField(blank=True, max_length=255, verbose_name='motivo da validação'),
        ),
    ]