"""
Django settings for aussprachetrainer project.

Generated by 'django-admin startproject' using Django 4.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
from aussprachetrainer.keyvault_manager import get_secret
from django.core.management.utils import get_random_secret_key  
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from django.core.files.storage import FileSystemStorage

def before_send(event, hint):
    return None  # Discarding all events

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
GITHUB_TEST = os.environ.get('DJANGO_GITHUB_TEST', 'False') == 'True'
IS_DOCKER_APP = os.environ.get('IS_DOCKER_APP', 'False') == 'True'
ENV = os.environ.get('ENVIRONMENT', 'production')
BETA = os.environ.get('BETA', 'False') == 'True'

if DEBUG:
    sentry_sdk.init(
        dsn= "https://8c306e7425f34fd94efa6d6a29331df4@o4505771582750720.ingest.sentry.io/4505771586420736",
        integrations=[DjangoIntegration()],
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
        # To set a uniform sample rate
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production,
        profiles_sample_rate=1.0,
        before_send=before_send # Wegmachen, wenn Errors getrackt werden sollen
    )

else:
    sentry_sdk.init(
        dsn= "https://8c306e7425f34fd94efa6d6a29331df4@o4505771582750720.ingest.sentry.io/4505771586420736",
        integrations=[DjangoIntegration()],
        send_default_pii=True,
        traces_sample_rate=1.0,
        profiles_sample_rate=0.5,
    )

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

SECRET_KEY = get_random_secret_key()


if DEBUG or ENV != "production":
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".ngrok-free.app", "0.0.0.0"]
else:
    ALLOWED_HOSTS = ["0.0.0.0", ".aussprachetrainer.org", "localhost", ".dakopen.de", "167.172.185.33"] # ip address of the server

ADMINS = [("Daniel Busch", "dakopen185@gmail.com")]

# Configure CORS
CORS_ALLOWED_ORIGINS = [
    "https://dakopen.de",
    'https://aussprachetrainer.org',
    # Add any other origins you want to allow
]

CSRF_TRUSTED_ORIGINS = ['https://*.dakopen.de','https://*.aussprachetrainer.org', 'https://dakopen.de', 'https://aussprachetrainer.org']

# Application definition

INSTALLED_APPS = [
    'user_auth',
    'frontend',
    'analyze',
    'dashboard',
    'learn',
    'fontawesomefree',
    'corsheaders',
    'storages',
    'django_celery_beat',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'aussprachetrainer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'aussprachetrainer.wsgi.application'

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

if DEBUG or ENV != "production":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    if not BETA:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'defaultdb',
                'USER': 'doadmin',
                'PASSWORD': get_secret("DO-DATABASE-PASSWORD"),
                'HOST': 'db-postgresql-fra-docker-do-user-10555764-0.c.db.ondigitalocean.com',  # This should match the service name in docker-compose
                'PORT': '25060',
                'OPTIONS': {
                    'sslmode': 'require',
                    'sslrootcert': os.path.join(BASE_DIR, 'certificates/ca-certificate.crt'),
                }
            }
        }

    else:  # BETA
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'defaultdb',
                'USER': 'doadmin',
                'PASSWORD': get_secret("BETA-DO-DATABASE-PASSWORD"),
                'HOST': 'dbaas-db-4088918-do-user-10555764-0.c.db.ondigitalocean.com',  # This should match the service name in docker-compose
                'PORT': '25060',
                'OPTIONS': {
                    'sslmode': 'require',
                    'sslrootcert': os.path.join(BASE_DIR, 'certificates/ca-certificate.crt'),
                }
            }
        }



AUTHENTICATION_BACKENDS = [
    'user_auth.backends.EmailOrUsernameModelBackend',
    'user_auth.backends.CaseInsensitiveModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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

# Authentication

AUTH_USER_MODEL = 'user_auth.CustomUser'
LOGIN_URL = '/auth/login/'


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'de'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_TZ = True

LANGUAGES = [
    ('de', 'German'),
    ('en', 'English'),
    # other languages...
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'frontend/locale'),
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

AWS_ACCESS_KEY_ID = get_secret('AWS-access-key-ID')
AWS_SECRET_ACCESS_KEY = get_secret('AWS-secret-access-key')
AWS_STORAGE_BUCKET_NAME = 'aussprachetrainer'
AWS_S3_ENDPOINT_URL = 'https://fra1.digitaloceanspaces.com'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

AWS_LOCATION = 'staticfiles'  # Optional: Use if you want to store files in a specific folder within your Space

# Static files settings
STATIC_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.{AWS_S3_ENDPOINT_URL}/{AWS_LOCATION}/static/'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

#
#STATIC_URL = 'static/'
#STATICFILES_DIRS = [  # unsure whether this is needed
#    BASE_DIR / "static",
#]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files settings (optional, if you want to serve user-uploaded files from Spaces)
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.nyc3.digitaloceanspaces.com/{AWS_LOCATION}/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
if DEBUG and not IS_DOCKER_APP:
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
else:
    CELERY_BROKER_URL = 'redis://redis:6379/0'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/0'

MS_SPEECH_SERVICES_API_KEY = get_secret("AzureSpeechKey1")
MS_SPEECH_SERVICES_REGION = "germanywestcentral"

DELETE_AUDIO_FILE_AFTER_ANALYSIS = True

# EMAIL SETTINGS:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.strato.de'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'kontakt@aussprachetrainer.org'
EMAIL_HOST_PASSWORD = get_secret("django-backend-email-host-password")
DEFAULT_FROM_EMAIL = 'AusspracheTrainer <kontakt@aussprachetrainer.org>'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

SECURE_FILE_STORAGE = FileSystemStorage(location=os.path.join(BASE_DIR, 'secure_storage'))