import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401, F403
from .base import SITE_ROLE, env_list


def required_env(name):
    value = os.environ.get(name)
    if value:
        return value
    raise ImproperlyConfigured(f'Missing required production environment variable: {name}')

DEBUG = False
SHOP_BASE_URL = os.environ.get('SHOP_BASE_URL', 'https://loja.marcosevegrand.com').rstrip('/')

PRODUCTION_ALLOWED_HOSTS_BY_ROLE = {
    'website': 'marcosevegrand.com,www.marcosevegrand.com',
    'shop': 'loja.marcosevegrand.com',
    'admin': 'admin.marcosevegrand.com',
}

ALLOWED_HOSTS = env_list(
    'ALLOWED_HOSTS',
    PRODUCTION_ALLOWED_HOSTS_BY_ROLE.get(
        SITE_ROLE,
        'marcosevegrand.com,www.marcosevegrand.com,loja.marcosevegrand.com,admin.marcosevegrand.com',
    ),
)

DB_PASSWORD = required_env('DB_PASSWORD')
EMAIL_HOST = required_env('EMAIL_HOST')
EMAIL_HOST_USER = required_env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = required_env('EMAIL_HOST_PASSWORD')

if PAYMENT_PROVIDER == 'stripe':
    STRIPE_SECRET_KEY = required_env('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = required_env('STRIPE_WEBHOOK_SECRET')
elif PAYMENT_PROVIDER == 'ifthenpay_mbway':
    IFTHENPAY_MBWAY_KEY = required_env('IFTHENPAY_MBWAY_KEY')
    IFTHENPAY_ANTI_PHISHING_KEY = required_env('IFTHENPAY_ANTI_PHISHING_KEY')

CSRF_TRUSTED_ORIGINS = [
    f'https://{host}'
    for host in ALLOWED_HOSTS
    if host != '*'
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'biobrassica'),
        'USER': os.environ.get('DB_USER', 'biobrassica'),
        'PASSWORD': DB_PASSWORD,
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 300,
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Email (Brevo SMTP or similar)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True

DJANGO_HTTPS_MODE = os.environ.get('DJANGO_HTTPS_MODE', 'proxy')
if DJANGO_HTTPS_MODE not in {'proxy', 'direct'}:
    raise ImproperlyConfigured(
        'DJANGO_HTTPS_MODE must be either "proxy" or "direct" in production.'
    )

# Static files — content-addressed so Cache-Control: immutable is safe.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage',
    },
}

# Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r'^_health/$']
if DJANGO_HTTPS_MODE == 'proxy':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

