from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0010_product_allow_shipping_and_order_fulfillment'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='categorytranslation',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='producttranslation',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='categorytranslation',
            constraint=models.UniqueConstraint(
                fields=('category', 'language'),
                name='catalog_unique_category_translation_language',
            ),
        ),
        migrations.AddConstraint(
            model_name='producttranslation',
            constraint=models.UniqueConstraint(
                fields=('product', 'language'),
                name='catalog_unique_product_translation_language',
            ),
        ),
    ]