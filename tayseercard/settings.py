import os
from pathlib import Path
import pymysql
import pymysql.converters
from pymysql.constants import FIELD_TYPE
from pymysql.converters import conversions


initializer_conv = pymysql.converters.conversions.copy()
pymysql.install_as_MySQLdb()
# Copier le dictionnaire de conversion par défaut
custom_conversions = conversions.copy()

# Forcer la conversion des types DATETIME et TIMESTAMP en vrais objets datetime Python
custom_conversions[FIELD_TYPE.DATETIME] = pymysql.converters.convert_datetime
custom_conversions[FIELD_TYPE.TIMESTAMP] = pymysql.converters.convert_datetime

# Associer ces règles de conversion à PyMySQL
pymysql.install_as_MySQLdb()

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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'exqxfpyq_admin_tayseerdb',       # Votre nom de base cPanel
        'USER': 'exqxfpyq_admin_tayseeruser',     # Votre utilisateur cPanel
        'PASSWORD': '47052333$ss',  # Votre mot de passe
        'HOST': 'localhost',
        'PORT': '3306',                     # Port standard MySQL
        'OPTIONS': {
            'conv': custom_conversions,  # On force Django à appliquer nos convertisseurs temporels
            'conv': initializer_conv,  # <--- Ajout crucial ici
            'charset': 'utf8mb4',
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

