import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {'1', 'true', 'yes', 'on'}


def env_list(name, default=''):
    value = os.environ.get(name, '').strip() or default
    return [item.strip() for item in value.split(',') if item.strip()]


def env_required(name, default=None):
    value = os.environ.get(name)
    if value:
        return value
    if env_bool('DJANGO_ALLOW_INSECURE_DEFAULTS') and default is not None:
        return default
    raise ImproperlyConfigured(f'Missing required environment variable: {name}')


SITE_URLCONFS = {
    'website': 'config.urls_website',
    'shop': 'config.urls_shop',
    'admin': 'config.urls_admin',
}

SITE_ROLE = os.environ.get('SITE_ROLE', '').strip().lower()
if SITE_ROLE and SITE_ROLE not in SITE_URLCONFS:
    raise ImproperlyConfigured('SITE_ROLE must be one of: website, shop, admin')

PAYMENT_PROVIDERS = {
    'stripe',
    'ifthenpay_mbway',
}


SECRET_KEY = env_required('DJANGO_SECRET_KEY', 'django-insecure-dev-only-change-in-production')

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.postgres',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_htmx',
    'apps.core',
    'apps.accounts',
    'apps.catalog',
    'apps.cart',
    'apps.orders',
    'apps.payments',
    'apps.website',
    'apps.content',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'config.middleware.SubdomainMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'config.middleware.SubdomainSecurityMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = SITE_URLCONFS.get(SITE_ROLE, 'config.urls_website')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.cart.context_processors.cart_count',
                'apps.core.context_processors.contact_locations',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# i18n
LANGUAGE_CODE = 'pt'
TIME_ZONE = 'Europe/Lisbon'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('pt', 'Português'),
    ('en', 'Inglês'),
    ('fr', 'Francês'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# Static & Media
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Payments
PAYMENT_PROVIDER = os.environ.get('PAYMENT_PROVIDER', 'stripe').strip().lower() or 'stripe'
if PAYMENT_PROVIDER not in PAYMENT_PROVIDERS:
    raise ImproperlyConfigured(
        'PAYMENT_PROVIDER must be one of: stripe, ifthenpay_mbway'
    )

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
STRIPE_CURRENCY = os.environ.get('STRIPE_CURRENCY', 'eur').strip().lower() or 'eur'
IFTHENPAY_API_BASE_URL = os.environ.get('IFTHENPAY_API_BASE_URL', 'https://api.ifthenpay.com').rstrip('/')
IFTHENPAY_MBWAY_KEY = os.environ.get('IFTHENPAY_MBWAY_KEY', '')
IFTHENPAY_ANTI_PHISHING_KEY = os.environ.get('IFTHENPAY_ANTI_PHISHING_KEY', '')
PAYMENTS_FORCE_DISABLED = env_bool('PAYMENTS_FORCE_DISABLED', default=False)
DEFAULT_SHOP_HOST = os.environ.get('SHOP_HOST', 'loja.marcosevegrand.com').strip() or 'loja.marcosevegrand.com'
SHOP_BASE_URL = (
    os.environ.get('SHOP_BASE_URL', '').strip() or f'https://{DEFAULT_SHOP_HOST}'
).rstrip('/')

# Email
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Biobrassica <loja@marcosevegrand.com>')
STAFF_NOTIFICATION_EMAILS = os.environ.get(
    'STAFF_NOTIFICATION_EMAILS', ''
).split(',') if os.environ.get('STAFF_NOTIFICATION_EMAILS') else []

PAYMENT_CALLBACK_RETENTION_DAYS = int(os.environ.get('PAYMENT_CALLBACK_RETENTION_DAYS', '30'))

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

LOG_LEVEL = os.environ.get('DJANGO_LOG_LEVEL', 'INFO').upper()

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'filters': ['redact_sensitive_data'],
        },
    },
    'filters': {
        'redact_sensitive_data': {
            '()': 'config.logging_filters.RedactingFilter',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'django.template': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps.orders': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'apps.payments': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}

# Unfold admin
UNFOLD = {
    'SITE_TITLE': 'Administração | Biobrassica',
    'SITE_HEADER': 'Biobrassica',
    'SITE_SYMBOL': None,
    'SITE_LOGO': '/static/images/brand/favicon_green.png',
    'DASHBOARD_CALLBACK': 'apps.core.admin_dashboard.build_admin_dashboard',
    'SITE_FAVICONS': [
        {'rel': 'icon', 'sizes': '32x32', 'href': '/static/images/brand/favicon_green.png'},
    ],
    'COLORS': {
        'primary': {
            '50': '#f4f7f4',
            '100': '#e0e8e1',
            '200': '#c1d1c2',
            '300': '#97b399',
            '400': '#6d946f',
            '500': '#3E5F46',
            '600': '#2C3F2D',
            '700': '#233224',
            '800': '#1a261b',
            '900': '#111a12',
            '950': '#090f0a',
        },
    },
    'SIDEBAR': {
        'navigation': [
            {
                'title': 'Operações',
                'icon': 'shopping_bag',
                'items': [
                    {'title': 'Encomendas', 'link': '/admin/orders/order/', 'icon': 'shopping_bag'},
                    {'title': 'Pagamentos', 'link': '/admin/payments/payment/', 'icon': 'payments'},
                ],
            },
            {
                'title': 'Catálogo',
                'icon': 'inventory_2',
                'items': [
                    {'title': 'Produtos', 'link': '/admin/catalog/product/', 'icon': 'inventory_2'},
                    {'title': 'Categorias', 'link': '/admin/catalog/category/', 'icon': 'category'},
                    {'title': 'Imagens de Produtos', 'link': '/admin/catalog/productimage/', 'icon': 'photo_library'},
                ],
            },
            {
                'title': 'Clientes',
                'icon': 'group',
                'items': [
                    {'title': 'Utilizadores', 'link': '/admin/accounts/user/', 'icon': 'person'},
                    {'title': 'Moradas', 'link': '/admin/accounts/address/', 'icon': 'location_on'},
                ],
            },
            {
                'title': 'Conteúdo',
                'icon': 'article',
                'items': [
                    {'title': 'Blog', 'link': '/admin/content/blogpost/', 'icon': 'edit_note'},
                    {'title': 'Receitas', 'link': '/admin/content/recipe/', 'icon': 'restaurant'},
                ],
            },
            {
                'title': 'Configurações',
                'icon': 'settings',
                'items': [
                    {'title': 'Localizações', 'link': '/admin/catalog/location/', 'icon': 'location_on'},
                    {'title': 'Métodos de Entrega', 'link': '/admin/catalog/deliverymethod/', 'icon': 'local_shipping'},
                ],
            },
        ],
    },
}
