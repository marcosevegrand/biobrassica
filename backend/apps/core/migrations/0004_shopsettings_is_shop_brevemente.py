from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_shopsettings_checkout_reservation'),
    ]

    operations = [
        migrations.AddField(
            model_name='shopsettings',
            name='is_shop_brevemente',
            field=models.BooleanField(
                default=False,
                help_text='Quando ativo, o subdomínio loja.* mostra uma página "Brevemente" e os botões da loja no site principal passam a dizer "Brevemente" em vez de linkarem para a loja.',
                verbose_name='modo brevemente',
            ),
        ),
    ]
