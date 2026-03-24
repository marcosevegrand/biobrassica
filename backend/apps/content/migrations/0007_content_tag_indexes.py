from django.contrib.postgres.indexes import GinIndex
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0006_translation_constraints'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='blogpost',
            index=GinIndex(fields=['tags'], name='content_blog_tags_gin'),
        ),
        migrations.AddIndex(
            model_name='recipe',
            index=GinIndex(fields=['tags'], name='content_recipe_tags_gin'),
        ),
    ]