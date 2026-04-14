from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0007_websitecontent_singleton'),
    ]

    operations = [
        migrations.AddField(
            model_name='websitecontent',
            name='company_address',
            field=models.TextField(blank=True, verbose_name='morada legal'),
        ),
        migrations.AddField(
            model_name='websitecontent',
            name='company_legal_name',
            field=models.CharField(blank=True, max_length=255, verbose_name='designação legal'),
        ),
        migrations.AddField(
            model_name='websitecontent',
            name='company_nif',
            field=models.CharField(blank=True, max_length=20, verbose_name='NIF da empresa'),
        ),
        migrations.AddField(
            model_name='websitecontent',
            name='support_email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='email de apoio'),
        ),
    ]