from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_order_fulfillment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='language',
            field=models.CharField(choices=[('pt', 'Português'), ('en', 'Inglês'), ('fr', 'Francês')], default='pt', max_length=2, verbose_name='idioma'),
        ),
    ]