from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0016_location_pickup_location_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='pickup_hours',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    'Horário de levantamento por dia da semana '
                    '(mon, tue, wed, thu, fri, sat, sun). '
                    'Ex: {"mon": "09:00–18:00"}.'
                ),
                verbose_name='horário de levantamento',
            ),
        ),
    ]
