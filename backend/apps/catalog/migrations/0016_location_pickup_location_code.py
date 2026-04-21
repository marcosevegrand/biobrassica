from django.db import migrations, models
from django.db.models import Q


def populate_pickup_location_codes(apps, schema_editor):
    Location = apps.get_model('catalog', 'Location')

    for location in Location.objects.filter(pickup_location_code=''):
        normalized_name = (location.name or '').strip().lower()
        pickup_location_code = ''
        if 'guimar' in normalized_name:
            pickup_location_code = 'guimaraes'
        elif 'braga' in normalized_name:
            pickup_location_code = 'braga'

        if pickup_location_code:
            location.pickup_location_code = pickup_location_code
            location.save(update_fields=['pickup_location_code'])


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0015_product_is_preview_only'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='pickup_location_code',
            field=models.CharField(
                blank=True,
                choices=[('braga', 'Braga'), ('guimaraes', 'Guimaraes')],
                help_text='Liga a localização a uma opção fixa de levantamento usada no checkout.',
                max_length=20,
                verbose_name='código de levantamento',
            ),
        ),
        migrations.RunPython(populate_pickup_location_codes, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='location',
            constraint=models.UniqueConstraint(
                condition=~Q(pickup_location_code=''),
                fields=('pickup_location_code',),
                name='catalog_unique_location_pickup_location_code',
            ),
        ),
    ]