from pathlib import Path

from decouple import config
from django.urls import reverse_lazy
import pymysql
pymysql.install_as_MySQLdb()


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-1234567890abcdefg')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,192.168.100.54',
    cast=lambda v: [s.strip() for s in v.split(',')],
)

INSTALLED_APPS = [
    'users',
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'common',
    'pages',
    'blogs',
    'products',
    'orders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Config.urls'

CSRF_TRUSTED_ORIGINS = [
    'http://192.168.100.54:8000',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

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
                'common.context_processors.shop',
            ],
        },
    },
]

WSGI_APPLICATION = 'Config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASS'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en'

LANGUAGES = (
    ('uz', 'Uzbek'),
    ('en', 'English'),
)

LOCALE_PATHS = (BASE_DIR / 'locale',)

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True

# ── Static fayllar ──────────────────────────────────────────
STATIC_URL = '/staticfiles/'
STATICFILES_DIRS = [BASE_DIR / 'assets/']
STATIC_ROOT = BASE_DIR / 'staticfiles/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── Media fayllar ───────────────────────────────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media/'
PRIVATE_MEDIA_ROOT = BASE_DIR / 'private_media/'   # e-kitob va to'liq audio shu yerda (ochiq URL yo'q)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Email ────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='sandbox.smtp.mailtrap.io')
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_PORT = config('EMAIL_PORT', default=2525, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='test@mailtrap.io')

LOGIN_URL = reverse_lazy("users:login")
# ── Do'kon sozlamalari (kerak bo'lsa .env orqali o'zgartiring) ───────────
LOGIN_URL = reverse_lazy('users:login')

SHOP_PHONE = config('SHOP_PHONE', default='+998 95 897 54 52')
SHOP_EMAIL = config('SHOP_EMAIL', default='support@domain.com')
SHOP_INSTAGRAM = config('SHOP_INSTAGRAM', default='https://www.instagram.com/shefbooks/')
SHOP_YOUTUBE = config('SHOP_YOUTUBE', default='https://www.youtube.com/@Shefbooks')
SHOP_TELEGRAM = config('SHOP_TELEGRAM', default='')

UZPOST_DELIVERY_FEE = config('UZPOST_DELIVERY_FEE', default=20000, cast=int)

PAYMENT_CARD_NUMBER = config('PAYMENT_CARD_NUMBER', default='5614 6812 5665 1260')
PAYMENT_CARD_HOLDER = config('PAYMENT_CARD_HOLDER', default="IBROHIMOV AKROMXO'JA")
