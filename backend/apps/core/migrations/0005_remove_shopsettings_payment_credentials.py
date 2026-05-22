from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_shopsettings_is_shop_brevemente'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shopsettings',
            name='bank_beneficiary',
        ),
        migrations.RemoveField(
            model_name='shopsettings',
            name='bank_bic',
        ),
        migrations.RemoveField(
            model_name='shopsettings',
            name='bank_iban',
        ),
        migrations.RemoveField(
            model_name='shopsettings',
            name='mbway_number',
        ),
    ]
