from django.db import migrations, models


def instructions_text_to_list(apps, schema_editor):
    """Convert existing text instructions to a single-item list."""
    RecipeTranslation = apps.get_model('content', 'RecipeTranslation')
    db_alias = schema_editor.connection.alias
    for tr in RecipeTranslation.objects.using(db_alias).all():
        text = tr.instructions_old or ''
        text = text.strip()
        tr.instructions = [text] if text else []
        tr.save(update_fields=['instructions'])


def instructions_list_to_text(apps, schema_editor):
    """Reverse: flatten list back to text (joined by newline)."""
    RecipeTranslation = apps.get_model('content', 'RecipeTranslation')
    db_alias = schema_editor.connection.alias
    for tr in RecipeTranslation.objects.using(db_alias).all():
        steps = tr.instructions or []
        tr.instructions_old = '\n\n'.join(str(s) for s in steps)
        tr.save(update_fields=['instructions_old'])


class Migration(migrations.Migration):
    # Must run outside a transaction: mixes DDL (ALTER TABLE) with DML (UPDATE)
    # which causes "pending trigger events" in PostgreSQL when atomic=True.
    atomic = False

    dependencies = [
        ('content', '0001_initial'),
    ]

    operations = [
        # 1. Add a temporary column to hold old text value during migration
        migrations.AddField(
            model_name='recipetranslation',
            name='instructions_old',
            field=models.TextField(blank=True, default=''),
        ),
        # 2. Copy text → temp column
        migrations.RunSQL(
            sql='UPDATE content_recipetranslation SET instructions_old = instructions',
            reverse_sql='UPDATE content_recipetranslation SET instructions = instructions_old',
        ),
        # 3. Drop old text column
        migrations.RemoveField(
            model_name='recipetranslation',
            name='instructions',
        ),
        # 4. Add new JSONField
        migrations.AddField(
            model_name='recipetranslation',
            name='instructions',
            field=models.JSONField(
                default=list,
                help_text='Lista de passos de preparação: ["Pré-aquecer o forno...", "Misturar..."]',
            ),
        ),
        # 5. Migrate data: text → list
        migrations.RunPython(instructions_text_to_list, instructions_list_to_text),
        # 6. Drop the temporary column
        migrations.RemoveField(
            model_name='recipetranslation',
            name='instructions_old',
        ),
        # 7. Update ingredients help_text
        migrations.AlterField(
            model_name='recipetranslation',
            name='ingredients',
            field=models.JSONField(
                default=list,
                help_text='Lista de ingredientes: ["200g farinha", "2 ovos", ...]',
            ),
        ),
    ]
