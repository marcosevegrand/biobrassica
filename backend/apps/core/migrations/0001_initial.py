from django.db import migrations, models
import django.core.validators


def copy_from_website_content(apps, schema_editor):
    ShopSettings = apps.get_model('core', 'ShopSettings')
    WebsiteContent = apps.get_model('website', 'WebsiteContent')

    website = WebsiteContent.objects.filter(pk=1).first()
    defaults = {}
    if website is not None:
        if hasattr(website, 'payments_enabled'):
            defaults['is_shop_active'] = bool(website.payments_enabled)
        if hasattr(website, 'manual_mbway_number'):
            number = (website.manual_mbway_number or '').strip()
            defaults['mbway_number'] = number
            defaults['mbway_enabled'] = bool(number)
    ShopSettings.objects.update_or_create(pk=1, defaults=defaults)


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('website', '0010_websitecontent_manual_mbway_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShopSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_shop_active', models.BooleanField(default=True, help_text='Quando desativado, os clientes não conseguem avançar do carrinho para o pagamento. Ideal para pausar a loja entre deployments ou em períodos de inatividade.', verbose_name='loja ativa')),
                ('min_order_total', models.DecimalField(decimal_places=2, default=0, help_text='Encomendas com total inferior a este valor são bloqueadas no checkout.', max_digits=8, validators=[django.core.validators.MinValueValidator(0)], verbose_name='valor mínimo de encomenda (€)')),
                ('mbway_enabled', models.BooleanField(default=True, verbose_name='aceitar MB WAY')),
                ('mbway_number', models.CharField(blank=True, help_text='Telemóvel mostrado ao cliente para pagar manualmente por MB WAY.', max_length=20, verbose_name='número MB WAY')),
                ('bank_transfer_enabled', models.BooleanField(default=False, verbose_name='aceitar transferência bancária')),
                ('bank_beneficiary', models.CharField(blank=True, max_length=120, verbose_name='nome do beneficiário')),
                ('bank_iban', models.CharField(blank=True, max_length=34, verbose_name='IBAN')),
                ('bank_bic', models.CharField(blank=True, max_length=11, verbose_name='BIC/SWIFT')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
            ],
            options={
                'verbose_name': 'configurações da loja',
                'verbose_name_plural': 'configurações da loja',
            },
        ),
        migrations.AddConstraint(
            model_name='shopsettings',
            constraint=models.CheckConstraint(condition=models.Q(('pk', 1)), name='core_shopsettings_singleton_pk_1'),
        ),
        migrations.RunPython(copy_from_website_content, noop),
    ]
