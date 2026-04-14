from django.db import migrations, models


def collapse_website_content_to_singleton(apps, schema_editor):
    WebsiteContent = apps.get_model('website', 'WebsiteContent')
    records = list(WebsiteContent.objects.order_by('pk'))
    if not records:
        return

    survivor = records[0]
    field_values = {
        field.attname: getattr(survivor, field.attname)
        for field in WebsiteContent._meta.concrete_fields
        if field.name != 'id'
    }

    WebsiteContent.objects.all().delete()
    WebsiteContent.objects.create(id=1, **field_values)


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0006_seed_websitecontent'),
    ]

    operations = [
        migrations.RunPython(collapse_website_content_to_singleton, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='websitecontent',
            constraint=models.CheckConstraint(
                condition=models.Q(('pk', 1)),
                name='website_singleton_pk_1',
            ),
        ),
    ]