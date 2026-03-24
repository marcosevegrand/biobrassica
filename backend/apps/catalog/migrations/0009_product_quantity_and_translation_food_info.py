from django.db import migrations, models


def _format_quantity(product):
    unit_quantity = getattr(product, 'unit_quantity', None)
    if unit_quantity is not None:
        amount = format(unit_quantity, 'f').rstrip('0').rstrip('.')
        amount = amount or '0'
        return f'{amount} g'

    price_unit = (getattr(product, 'price_unit', '') or '').strip()
    return price_unit


def forwards(apps, schema_editor):
    Product = apps.get_model('catalog', 'Product')
    ProductTranslation = apps.get_model('catalog', 'ProductTranslation')

    for product in Product.objects.all().iterator():
        quantity = _format_quantity(product)
        Product.objects.filter(pk=product.pk).update(quantity=quantity)

        translations = ProductTranslation.objects.filter(product_id=product.pk)
        translations.update(
            allergens=(product.modifiers or '').strip(),
            ingredients=(product.ingredients or '').strip(),
        )


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0008_product_brand'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='quantity',
            field=models.CharField(default='', help_text='Ex: 500 g, 1 un, 6 x 330 ml', max_length=80, verbose_name='quantidade'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='producttranslation',
            name='allergens',
            field=models.CharField(default='', help_text='Ex: Contém glúten, soja, frutos secos', max_length=255, verbose_name='alergénicos'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='producttranslation',
            name='ingredients',
            field=models.TextField(default='', help_text='Lista completa de ingredientes do produto.', verbose_name='ingredientes'),
            preserve_default=False,
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='product',
            name='ingredients',
        ),
        migrations.RemoveField(
            model_name='product',
            name='modifiers',
        ),
        migrations.RemoveField(
            model_name='product',
            name='price_unit',
        ),
        migrations.RemoveField(
            model_name='product',
            name='unit_quantity',
        ),
    ]