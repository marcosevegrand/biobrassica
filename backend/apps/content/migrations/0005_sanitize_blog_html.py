from django.db import migrations


def sanitize_blog_html(apps, schema_editor):
    BlogPostTranslation = apps.get_model('content', 'BlogPostTranslation')

    from apps.content.sanitization import sanitize_html

    for translation in BlogPostTranslation.objects.exclude(content='').iterator(chunk_size=200):
        sanitized_content = sanitize_html(translation.content)
        if sanitized_content != translation.content:
            translation.content = sanitized_content
            translation.save(update_fields=['content'])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0004_alter_blogpost_author_alter_blogpost_cover_image_and_more'),
    ]

    operations = [
        migrations.RunPython(sanitize_blog_html, migrations.RunPython.noop),
    ]