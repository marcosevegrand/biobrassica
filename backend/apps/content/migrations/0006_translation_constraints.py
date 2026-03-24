from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0005_sanitize_blog_html'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='blogposttranslation',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='recipetranslation',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='blogposttranslation',
            constraint=models.UniqueConstraint(
                fields=('blog_post', 'language'),
                name='content_unique_blog_translation_language',
            ),
        ),
        migrations.AddConstraint(
            model_name='recipetranslation',
            constraint=models.UniqueConstraint(
                fields=('recipe', 'language'),
                name='content_unique_recipe_translation_language',
            ),
        ),
    ]