import os

from .base import *  # noqa: F401, F403

DEBUG = True
SECURE_SSL_REDIRECT = False
SHOP_HOST = os.environ.get('SHOP_HOST', 'loja.lvh.me').strip() or 'loja.lvh.me'
SHOP_BASE_URL = f'https://{SHOP_HOST}'.rstrip('/')

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    # lvh.me resolves to 127.0.0.1 — use for subdomain testing
    'lvh.me',
    'loja.lvh.me',
    'admin.lvh.me',
    'loja.localhost',
    'admin.localhost',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Email: Mailpit for dev (web UI at http://localhost:8025)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'mailpit')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '1025'))
EMAIL_USE_TLS = False
