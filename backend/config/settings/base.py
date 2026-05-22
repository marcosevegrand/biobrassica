import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {'1', 'true', 'yes', 'on'}


def env_value(name, default=''):
    return os.environ.get(name, '').strip() or default


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


def dedupe_list(items):
    return list(dict.fromkeys(item for item in items if item))


def domain_hosts(role, domains):
    role_prefixes = {
        'website': ('', 'www'),
        'shop': ('loja',),
        'admin': ('admin',),
    }
    return dedupe_list(
        domain if prefix == '' else f'{prefix}.{domain}'
        for domain in domains
        for prefix in role_prefixes[role]
    )


PRIMARY_DOMAIN = env_value('PRIMARY_DOMAIN', 'biobrassica.pt')
DOMAIN_ALIASES = env_list('DOMAIN_ALIASES')
PUBLIC_DOMAINS = dedupe_list([PRIMARY_DOMAIN, *DOMAIN_ALIASES])

WEBSITE_HOST = env_value('WEBSITE_HOST', PRIMARY_DOMAIN)
WEBSITE_ALLOWED_HOSTS = env_list(
    'WEBSITE_ALLOWED_HOSTS',
    ','.join(domain_hosts('website', PUBLIC_DOMAINS)),
)
SHOP_HOST = env_value('SHOP_HOST', f'loja.{PRIMARY_DOMAIN}')
SHOP_ALLOWED_HOSTS = env_list(
    'SHOP_ALLOWED_HOSTS',
    ','.join(domain_hosts('shop', PUBLIC_DOMAINS)),
)
ADMIN_HOST = env_value('ADMIN_HOST', f'admin.{PRIMARY_DOMAIN}')
ADMIN_ALLOWED_HOSTS = env_list(
    'ADMIN_ALLOWED_HOSTS',
    ','.join(domain_hosts('admin', PUBLIC_DOMAINS)),
)

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
    'config.middleware.ShopBrevementeMiddleware',
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

# Payments — manual flows only.
# Method toggles stay in ShopSettings, but payment credentials are sensitive
# and must come from environment variables instead of the admin backoffice.
SHOP_BASE_URL = f'https://{SHOP_HOST}'.rstrip('/')
MANUAL_MBWAY_NUMBER = env_value('MANUAL_MBWAY_NUMBER')
BANK_TRANSFER_BENEFICIARY = env_value('BANK_TRANSFER_BENEFICIARY')
BANK_TRANSFER_IBAN = env_value('BANK_TRANSFER_IBAN')
BANK_TRANSFER_BIC = env_value('BANK_TRANSFER_BIC')

# Email
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Biobrassica <loja@biobrassica.pt>')
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
    'STYLES': [
        lambda request: '/static/css/admin/required_fields.css',
    ],
    'SCRIPTS': [
        lambda request: '/static/js/admin/required_fields.js',
        lambda request: '/static/js/admin/product_editor.js',
    ],
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
                    {'title': 'Painel', 'link': '/admin/operacoes/painel/', 'icon': 'dashboard'},
                    {'title': 'Encomendas', 'link': '/admin/orders/order/', 'icon': 'shopping_bag'},
                    {'title': 'Pagamentos', 'link': '/admin/payments/payment/', 'icon': 'payments'},
                    {'title': 'Clientes', 'link': '/admin/accounts/user/', 'icon': 'group'},
                ],
            },
            {
                'title': 'Equipa',
                'icon': 'admin_panel_settings',
                'items': [
                    {'title': 'Equipa', 'link': '/admin/accounts/staffaccount/', 'icon': 'admin_panel_settings'},
                ],
            },
            {
                'title': 'Catálogo',
                'icon': 'inventory_2',
                'items': [
                    {'title': 'Categorias', 'link': '/admin/catalog/category/', 'icon': 'category'},
                    {'title': 'Produtos', 'link': '/admin/catalog/product/', 'icon': 'inventory_2'},
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
                    {'title': 'Configurações', 'link': '/admin/core/shopsettings/', 'icon': 'tune'},
                ],
            },
        ],
    },
}

# Instagram post shortcodes used by the fetch_instagram_posts management command.
# Populate this list with shortcodes from https://www.instagram.com/biobrassica/
INSTAGRAM_POST_SHORTCODES: list[str] = []
