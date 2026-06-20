import os
from pathlib import Path
from pathlib import Path

# ------------------------------------------------------------------
# MySQL / PyMySQL configuration (optional)
# ------------------------------------------------------------------
try:
    import pymysql               # noqa: F401
    import pymysql.converters    # noqa: F401
    from pymysql.constants import FIELD_TYPE  # noqa: F401
    from pymysql.converters import conversions  # noqa: F401

    # Keep a copy of the default conversion map
    initializer_conv = pymysql.converters.conversions.copy()
    pymysql.install_as_MySQLdb()

    # Custom conversion rules
    custom_conversions = conversions.copy()
    custom_conversions[FIELD_TYPE.DATETIME] = pymysql.converters.convert_datetime
    custom_conversions[FIELD_TYPE.TIMESTAMP] = pymysql.converters.convert_datetime

    # Apply the custom converters to Django’s MySQL backend
    pymysql.install_as_MySQLdb()
except ImportError:
    # PyMySQL isn’t installed – fall back to the default MySQL client.
    initializer_conv = {}
    custom_conversions = {}

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'change-this-in-production'

DEBUG = True  # Set to False in production

ALLOWED_HOSTS = ['tayseercard.com', 'www.tayseercard.com', '*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.accounts',
    'apps.stores',
    'apps.vouchers',
    'apps.scanning',
  
]

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files on VPS
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tayseercard.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.accounts.context_processors.admin_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'tayseercard.wsgi.application'

if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Production MySQL configuration (Octenium / phpMyAdmin)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('MYSQL_DB_NAME', 'octenium_db'),
            'USER': os.getenv('MYSQL_USER', 'octenium_user'),
            'PASSWORD': os.getenv('MYSQL_PASSWORD', 'octenium_pass'),
            'HOST': os.getenv('MYSQL_HOST', 'octenium_host'),
            'PORT': os.getenv('MYSQL_PORT', '3306'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
                # Merge custom converters if you still use PyMySQL
                'conv': {**initializer_conv, **custom_conversions},
            },
        }
    }
AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'public_html/static/')
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Algiers'
USE_I18N = True
USE_TZ = False

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@tayseercard.com'
