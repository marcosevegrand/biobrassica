from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0009_product_quantity_and_translation_food_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='allow_shipping',
            field=models.BooleanField(default=False, help_text='Quando ativo, o produto pode ser enviado. Caso contrário, fica disponível apenas para levantamento em loja.', verbose_name='permite envio'),
        ),
    ]