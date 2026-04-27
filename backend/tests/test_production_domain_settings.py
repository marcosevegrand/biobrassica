import importlib
import os
from unittest.mock import patch

from django.test import SimpleTestCase


class ProductionDomainSettingsTests(SimpleTestCase):
    def load_production_settings(self, **extra_env):
        env = {
            'DJANGO_SECRET_KEY': 'test-secret',
            'DB_PASSWORD': 'test-db-password',
            'EMAIL_HOST': 'smtp.example.com',
            'EMAIL_HOST_USER': 'mailer@example.com',
            'EMAIL_HOST_PASSWORD': 'test-email-password',
            'PAYMENT_PROVIDER': 'stripe',
            'STRIPE_SECRET_KEY': 'sk_test_123',
            'STRIPE_WEBHOOK_SECRET': 'whsec_test_123',
        }
        env.update(extra_env)

        with patch.dict(os.environ, env, clear=False):
            base_settings = importlib.import_module('config.settings.base')
            production_settings = importlib.import_module('config.settings.production')
            importlib.reload(base_settings)
            return importlib.reload(production_settings)

    def test_shop_base_url_defaults_to_configured_shop_host(self):
        settings_module = self.load_production_settings(
            SITE_ROLE='website',
            SHOP_HOST='loja.biobrassica.pt',
            SHOP_BASE_URL='',
            ALLOWED_HOSTS='',
        )

        self.assertEqual(settings_module.SHOP_BASE_URL, 'https://loja.biobrassica.pt')

    def test_role_specific_allowed_hosts_drive_defaults(self):
        settings_module = self.load_production_settings(
            SITE_ROLE='website',
            ALLOWED_HOSTS='',
            WEBSITE_ALLOWED_HOSTS='biobrassica.pt,www.biobrassica.pt,marcosevegrand.com',
            SHOP_ALLOWED_HOSTS='loja.biobrassica.pt,loja.marcosevegrand.com',
            ADMIN_ALLOWED_HOSTS='admin.biobrassica.pt,admin.marcosevegrand.com',
        )

        self.assertEqual(
            settings_module.ALLOWED_HOSTS,
            ['biobrassica.pt', 'www.biobrassica.pt', 'marcosevegrand.com'],
        )
        self.assertEqual(
            settings_module.CSRF_TRUSTED_ORIGINS,
            [
                'https://biobrassica.pt',
                'https://www.biobrassica.pt',
                'https://marcosevegrand.com',
            ],
        )