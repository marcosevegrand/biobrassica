from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0013_primary_product_image_constraint'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='available_locations',
            field=models.ManyToManyField(
                blank=True,
                related_name='products',
                to='catalog.location',
                verbose_name='localizações',
            ),
        ),
    ]