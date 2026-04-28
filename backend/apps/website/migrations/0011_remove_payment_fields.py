from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0010_websitecontent_manual_mbway_number'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='websitecontent',
            name='payments_enabled',
        ),
        migrations.RemoveField(
            model_name='websitecontent',
            name='manual_mbway_number',
        ),
    ]
