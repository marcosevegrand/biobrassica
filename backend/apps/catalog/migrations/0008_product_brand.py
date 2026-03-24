from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0007_alter_product_bio_code_alter_product_ingredients_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='brand',
            field=models.CharField(default='', help_text='Marca do produto.', max_length=120, verbose_name='marca'),
            preserve_default=False,
        ),
    ]