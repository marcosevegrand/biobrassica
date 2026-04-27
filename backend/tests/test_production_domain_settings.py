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

    def test_shop_base_url_defaults_to_derived_shop_host(self):
        settings_module = self.load_production_settings(
            SITE_ROLE='website',
            PRIMARY_DOMAIN='biobrassica.pt',
            ALLOWED_HOSTS='',
        )

        self.assertEqual(settings_module.SHOP_BASE_URL, 'https://loja.biobrassica.pt')

    def test_domain_aliases_drive_role_specific_host_defaults(self):
        settings_module = self.load_production_settings(
            SITE_ROLE='website',
            PRIMARY_DOMAIN='biobrassica.pt',
            DOMAIN_ALIASES='marcosevegrand.com',
            ALLOWED_HOSTS='',
        )

        self.assertEqual(settings_module.WEBSITE_HOST, 'biobrassica.pt')
        self.assertEqual(settings_module.SHOP_HOST, 'loja.biobrassica.pt')
        self.assertEqual(settings_module.ADMIN_HOST, 'admin.biobrassica.pt')
        self.assertEqual(
            settings_module.ALLOWED_HOSTS,
            [
                'biobrassica.pt',
                'www.biobrassica.pt',
                'marcosevegrand.com',
                'www.marcosevegrand.com',
            ],
        )
        self.assertEqual(
            settings_module.CSRF_TRUSTED_ORIGINS,
            [
                'https://biobrassica.pt',
                'https://www.biobrassica.pt',
                'https://marcosevegrand.com',
                'https://www.marcosevegrand.com',
            ],
        )

    def test_explicit_host_overrides_still_win(self):
        settings_module = self.load_production_settings(
            SITE_ROLE='shop',
            PRIMARY_DOMAIN='biobrassica.pt',
            DOMAIN_ALIASES='marcosevegrand.com',
            SHOP_HOST='shop.biobrassica.pt',
            SHOP_ALLOWED_HOSTS='shop.biobrassica.pt,shop.marcosevegrand.com',
            ALLOWED_HOSTS='',
        )

        self.assertEqual(settings_module.SHOP_HOST, 'shop.biobrassica.pt')
        self.assertEqual(
            settings_module.ALLOWED_HOSTS,
            ['shop.biobrassica.pt', 'shop.marcosevegrand.com'],
        )

    def test_manual_mbway_provider_does_not_require_gateway_credentials(self):
        settings_module = self.load_production_settings(
            PAYMENT_PROVIDER='mbway_manual',
            STRIPE_SECRET_KEY='',
            STRIPE_WEBHOOK_SECRET='',
            IFTHENPAY_MBWAY_KEY='',
            IFTHENPAY_ANTI_PHISHING_KEY='',
        )

        self.assertEqual(settings_module.PAYMENT_PROVIDER, 'mbway_manual')