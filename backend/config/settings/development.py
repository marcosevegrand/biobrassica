import os

from .base import *  # noqa: F401, F403

DEBUG = True
SECURE_SSL_REDIRECT = False
SHOP_BASE_URL = os.environ.get('SHOP_BASE_URL', 'https://loja.lvh.me').rstrip('/')

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
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'biobrassica'),
        'USER': os.environ.get('DB_USER', 'biobrassica'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'biobrassica'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
    }
}

# Email: Mailpit for dev (web UI at http://localhost:8025)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'mailpit')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '1025'))
EMAIL_USE_TLS = False
