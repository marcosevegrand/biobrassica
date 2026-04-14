from django.db import migrations, models
from django.db.models import Q


def dedupe_primary_product_images(apps, schema_editor):
    ProductImage = apps.get_model('catalog', 'ProductImage')

    product_ids = (
        ProductImage.objects.filter(is_primary=True)
        .values_list('product_id', flat=True)
        .distinct()
    )

    for product_id in product_ids:
        primary_images = list(
            ProductImage.objects.filter(product_id=product_id, is_primary=True)
            .order_by('order', 'pk')
        )
        for image in primary_images[1:]:
            image.is_primary = False
            image.save(update_fields=['is_primary'])


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0012_location_content_fields'),
    ]

    operations = [
        migrations.RunPython(dedupe_primary_product_images, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='productimage',
            constraint=models.UniqueConstraint(
                fields=('product',),
                condition=Q(('is_primary', True)),
                name='catalog_unique_primary_product_image',
            ),
        ),
    ]