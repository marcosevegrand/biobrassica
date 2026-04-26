from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_address_is_default_alter_address_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='country',
            field=models.CharField(choices=[('PT', 'Portugal')], default='PT', max_length=2, verbose_name='País'),
        ),
    ]