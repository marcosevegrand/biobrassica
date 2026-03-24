from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0011_translation_constraints'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='email'),
        ),
        migrations.AddField(
            model_name='location',
            name='image',
            field=models.ImageField(blank=True, upload_to='locations/', verbose_name='imagem'),
        ),
        migrations.AddField(
            model_name='location',
            name='map_embed_url',
            field=models.URLField(blank=True, verbose_name='mapa embutido'),
        ),
        migrations.AddField(
            model_name='location',
            name='opening_hours',
            field=models.CharField(blank=True, max_length=120, verbose_name='horário'),
        ),
        migrations.AddField(
            model_name='location',
            name='phone',
            field=models.CharField(blank=True, max_length=20, verbose_name='telefone'),
        ),
    ]