from pathlib import Path

from django.test import SimpleTestCase


class NginxConfigTests(SimpleTestCase):
    def test_shop_and_admin_csp_allow_alpine_expression_evaluation(self):
        repo_root = Path(__file__).resolve().parents[2]
        app_conf = (repo_root / 'nginx' / 'conf.d' / 'app.conf').read_text(encoding='utf-8')

        self.assertGreaterEqual(app_conf.count("script-src 'self' 'unsafe-inline' 'unsafe-eval'"), 2)