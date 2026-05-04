from django.db import migrations, models


def forwards_catalog_pt_first(apps, schema_editor):
    Category = apps.get_model('catalog', 'Category')
    CategoryPosition = apps.get_model('catalog', 'CategoryPosition')
    CategoryTranslation = apps.get_model('catalog', 'CategoryTranslation')
    DeliveryMethod = apps.get_model('catalog', 'DeliveryMethod')
    DeliveryMethodPosition = apps.get_model('catalog', 'DeliveryMethodPosition')
    Location = apps.get_model('catalog', 'Location')
    LocationPosition = apps.get_model('catalog', 'LocationPosition')
    Product = apps.get_model('catalog', 'Product')
    ProductImage = apps.get_model('catalog', 'ProductImage')
    ProductTranslation = apps.get_model('catalog', 'ProductTranslation')

    for location in Location.objects.order_by('order', 'name', 'pk'):
        LocationPosition.objects.update_or_create(
            location=location,
            defaults={'position': location.order},
        )

    for delivery_method in DeliveryMethod.objects.order_by('order', 'name', 'pk'):
        DeliveryMethodPosition.objects.update_or_create(
            delivery_method=delivery_method,
            defaults={'position': delivery_method.order},
        )

    for category in Category.objects.order_by('order', 'pk'):
        pt_translation = CategoryTranslation.objects.filter(category=category, language='pt').order_by('pk').first()
        category.name = (pt_translation.name if pt_translation and pt_translation.name else category.slug).strip()
        category.save(update_fields=['name'])
        CategoryPosition.objects.update_or_create(
            category=category,
            defaults={'position': category.order},
        )

    for product in Product.objects.order_by('pk'):
        pt_translation = ProductTranslation.objects.filter(product=product, language='pt').order_by('pk').first()
        if pt_translation is not None:
            description_parts = [str(pt_translation.description or '').strip(), str(pt_translation.ingredients or '').strip()]
            product.name = str(pt_translation.name or product.slug).strip()
            product.description = '\n\n'.join(part for part in description_parts if part)
            product.allergens = str(pt_translation.allergens or '').strip()
        else:
            product.name = str(product.slug or '').replace('-', ' ').strip()
            product.description = ''
            product.allergens = ''

        primary_image = ProductImage.objects.filter(product=product, is_primary=True).order_by('order', 'pk').first()
        fallback_image = ProductImage.objects.filter(product=product).order_by('order', 'pk').first()
        chosen_image = primary_image or fallback_image
        if chosen_image is not None:
            product.image = chosen_image.image

        product.allow_pickup = product.pickup_locations.exists()
        product.save(update_fields=['name', 'description', 'allergens', 'image', 'allow_pickup'])

    for category_translation in CategoryTranslation.objects.filter(language='pt'):
        category_translation.delete()

    for product_translation in ProductTranslation.objects.all().order_by('pk'):
        if product_translation.language == 'pt':
            product_translation.delete()
            continue

        ingredients = str(product_translation.ingredients or '').strip()
        description = str(product_translation.description or '').strip()
        if ingredients:
            product_translation.description = '\n\n'.join(part for part in [description, ingredients] if part)
            product_translation.save(update_fields=['description'])


def backwards_catalog_pt_first(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0017_location_pickup_hours'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='name',
            field=models.CharField(default='', max_length=255, verbose_name='nome'),
            preserve_default=False,
        ),
        migrations.RenameField(
            model_name='category',
            old_name='is_featured',
            new_name='is_special',
        ),
        migrations.RenameField(
            model_name='product',
            old_name='is_preview_only',
            new_name='is_preview',
        ),
        migrations.RenameField(
            model_name='product',
            old_name='available_locations',
            new_name='pickup_locations',
        ),
        migrations.AddField(
            model_name='product',
            name='name',
            field=models.CharField(default='', max_length=255, verbose_name='nome'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='description',
            field=models.TextField(default='', verbose_name='descrição comercial + ingredientes'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='allergens',
            field=models.CharField(default='', max_length=255, verbose_name='alergénicos'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='allow_pickup',
            field=models.BooleanField(default=True, verbose_name='recolha'),
        ),
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, default='', upload_to='products/', verbose_name='imagem'),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='LocationPosition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(default=0, verbose_name='posição')),
                ('location', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='sort_order', to='catalog.location', verbose_name='localização')),
            ],
            options={
                'verbose_name': 'ordem de localização',
                'verbose_name_plural': 'ordens de localização',
                'ordering': ['position', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='DeliveryMethodPosition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(default=0, verbose_name='posição')),
                ('delivery_method', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='sort_order', to='catalog.deliverymethod', verbose_name='método de entrega')),
            ],
            options={
                'verbose_name': 'ordem de método de entrega',
                'verbose_name_plural': 'ordens de métodos de entrega',
                'ordering': ['position', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='CategoryPosition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(default=0, verbose_name='posição')),
                ('category', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='sort_order', to='catalog.category', verbose_name='categoria')),
            ],
            options={
                'verbose_name': 'ordem de categoria',
                'verbose_name_plural': 'ordens de categoria',
                'ordering': ['position', 'pk'],
            },
        ),
        migrations.AddField(
            model_name='categorytranslation',
            name='featured_message',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='mensagem de destaque'),
            preserve_default=False,
        ),
        migrations.RunPython(forwards_catalog_pt_first, backwards_catalog_pt_first),
        migrations.RemoveField(
            model_name='location',
            name='order',
        ),
        migrations.RemoveField(
            model_name='deliverymethod',
            name='order',
        ),
        migrations.RemoveField(
            model_name='category',
            name='order',
        ),
        migrations.RemoveField(
            model_name='categorytranslation',
            name='description',
        ),
        migrations.AlterField(
            model_name='categorytranslation',
            name='language',
            field=models.CharField(choices=[('en', 'Inglês'), ('fr', 'Francês')], max_length=2, verbose_name='idioma'),
        ),
        migrations.RemoveField(
            model_name='producttranslation',
            name='ingredients',
        ),
        migrations.AlterField(
            model_name='producttranslation',
            name='language',
            field=models.CharField(choices=[('en', 'Inglês'), ('fr', 'Francês')], max_length=2, verbose_name='idioma'),
        ),
        migrations.AlterField(
            model_name='producttranslation',
            name='description',
            field=models.TextField(verbose_name='descrição comercial + ingredientes'),
        ),
        migrations.DeleteModel(
            name='ProductImage',
        ),
    ]
