from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0008_websitecontent_company_details'),
    ]

    operations = [
        migrations.AddField(
            model_name='websitecontent',
            name='payments_enabled',
            field=models.BooleanField(
                default=True,
                help_text='Desative temporariamente para bloquear novos pagamentos e novas sessões Stripe.',
                verbose_name='pagamentos ativos',
            ),
        ),
    ]