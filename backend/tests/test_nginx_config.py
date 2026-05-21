from pathlib import Path

from django.test import SimpleTestCase


class NginxConfigTests(SimpleTestCase):
    def _nginx_conf(self):
        repo_root = Path(__file__).resolve().parents[2]
        return (repo_root / 'nginx' / 'nginx.conf').read_text(encoding='utf-8')

    def _app_conf(self):
        repo_root = Path(__file__).resolve().parents[2]
        return (repo_root / 'nginx' / 'conf.d' / 'app.conf').read_text(encoding='utf-8')

    def test_shop_and_admin_csp_allow_alpine_expression_evaluation(self):
        app_conf = self._app_conf()

        self.assertGreaterEqual(app_conf.count("script-src 'self' 'unsafe-inline' 'unsafe-eval'"), 2)

    def test_media_locations_block_active_file_types(self):
        app_conf = self._app_conf()

        self.assertEqual(app_conf.count('location ~* ^/media/.*\\.(?:html?'), 3)
        for extension in ('svg', 'js', 'php', 'exe'):
            self.assertIn(extension, app_conf)

    def test_shop_csp_does_not_allow_external_script_cdn(self):
        app_conf = self._app_conf()

        self.assertNotIn('https://unpkg.com', app_conf)

    def test_global_nginx_hides_version_and_sets_tls_policy(self):
        nginx_conf = self._nginx_conf()

        self.assertIn('server_tokens off;', nginx_conf)
        self.assertIn('ssl_protocols TLSv1.2 TLSv1.3;', nginx_conf)
        self.assertIn('proxy_set_header X-Forwarded-Proto $scheme;', nginx_conf)
        self.assertNotIn('$http_x_forwarded_proto', nginx_conf)

    def test_https_locations_send_security_headers(self):
        app_conf = self._app_conf()

        self.assertEqual(app_conf.count('Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always'), 9)
        self.assertEqual(app_conf.count('X-Permitted-Cross-Domain-Policies "none" always'), 9)
        self.assertEqual(app_conf.count('Permissions-Policy "camera=(), microphone=(), geolocation=()" always'), 3)
