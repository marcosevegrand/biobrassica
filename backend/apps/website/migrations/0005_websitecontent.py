from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0004_alter_teammember_is_active_alter_teammember_name_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebsiteContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('home_hero_image', models.ImageField(blank=True, upload_to='website/', verbose_name='imagem hero home')),
                ('home_hero_title_line1', models.CharField(blank=True, max_length=120, verbose_name='título home linha 1')),
                ('home_hero_title_line2', models.CharField(blank=True, max_length=120, verbose_name='título home linha 2')),
                ('home_hero_tagline', models.CharField(blank=True, max_length=255, verbose_name='subtítulo home')),
                ('home_quote_text', models.TextField(blank=True, verbose_name='citação home')),
                ('home_quote_author', models.CharField(blank=True, max_length=120, verbose_name='autor da citação')),
                ('home_quote_role', models.CharField(blank=True, max_length=120, verbose_name='função do autor')),
                ('home_quote_image', models.ImageField(blank=True, upload_to='website/', verbose_name='imagem da citação')),
                ('home_shop_cta_title', models.CharField(blank=True, max_length=120, verbose_name='título CTA loja')),
                ('home_shop_cta_body', models.TextField(blank=True, verbose_name='texto CTA loja')),
                ('about_hero_image', models.ImageField(blank=True, upload_to='website/', verbose_name='imagem hero quem somos')),
                ('about_hero_title', models.CharField(blank=True, max_length=160, verbose_name='título hero quem somos')),
                ('about_hero_subtitle', models.CharField(blank=True, max_length=255, verbose_name='subtítulo hero quem somos')),
                ('about_meaning_title', models.CharField(blank=True, max_length=160, verbose_name='título bloco significado')),
                ('about_meaning_body', models.TextField(blank=True, verbose_name='texto bloco significado')),
                ('about_meaning_image', models.ImageField(blank=True, upload_to='website/', verbose_name='imagem bloco significado')),
                ('about_selection_title', models.CharField(blank=True, max_length=160, verbose_name='título bloco seleção')),
                ('about_selection_body', models.TextField(blank=True, verbose_name='texto bloco seleção')),
                ('about_selection_image', models.ImageField(blank=True, upload_to='website/', verbose_name='imagem bloco seleção')),
                ('about_farm_title', models.CharField(blank=True, max_length=160, verbose_name='título bloco quinta')),
                ('about_farm_body', models.TextField(blank=True, verbose_name='texto bloco quinta')),
                ('about_farm_image', models.ImageField(blank=True, upload_to='website/', verbose_name='imagem bloco quinta')),
                ('about_video_title', models.CharField(blank=True, max_length=160, verbose_name='título vídeo quem somos')),
                ('about_video_body', models.TextField(blank=True, verbose_name='texto vídeo quem somos')),
                ('agriculture_hero_image', models.ImageField(blank=True, upload_to='website/', verbose_name='imagem hero agricultura')),
                ('agriculture_intro_text', models.TextField(blank=True, verbose_name='introdução agricultura')),
                ('agriculture_why_title', models.CharField(blank=True, max_length=160, verbose_name='título porquê biológico')),
                ('agriculture_why_body', models.TextField(blank=True, verbose_name='texto porquê biológico')),
                ('agriculture_why_image', models.ImageField(blank=True, upload_to='website/', verbose_name='imagem porquê biológico')),
                ('contacts_hero_title', models.CharField(blank=True, max_length=160, verbose_name='título contactos')),
                ('contacts_hero_body', models.TextField(blank=True, verbose_name='texto contactos')),
                ('whatsapp_number', models.CharField(blank=True, max_length=20, verbose_name='número WhatsApp')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
            ],
            options={
                'verbose_name': 'conteúdo do website',
                'verbose_name_plural': 'conteúdo do website',
            },
        ),
    ]