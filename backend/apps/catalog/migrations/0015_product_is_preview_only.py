from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0014_alter_product_available_locations'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_preview_only',
            field=models.BooleanField(
                default=False,
                help_text='Quando ativo, o produto permanece visível no catálogo mas não pode ser comprado.',
                verbose_name='apenas pré-visualização',
            ),
        ),
    ]