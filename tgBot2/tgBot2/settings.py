import os
import redis

from pathlib import Path
from dotenv import load_dotenv
# Загружаем переменные из .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

if DEBUG:
    ALLOWED_HOSTS = ["*"]

else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', os.getenv("BASE_URL")]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
        # locations
    'django.contrib.gis',
        # bot
    'mainBot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tgBot2.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tgBot2.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# Разбираем ссылку на db в Docker
from urllib.parse import urlparse
# Разбор URL базы данных
url = urlparse(
f"postgres://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@db:5432/{os.getenv("POSTGRES_DB")}"
)                                                                        # db - имя контейнера

# Postgres v16
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': url.path[1:],  # Убираем ведущий символ '/'
        'USER': url.username,
        'PASSWORD': url.password,
        'HOST': url.hostname,
        'PORT': url.port,       
    }
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://redis:6379/1',  # redis - это имя контейнера
    }
}
CACHE_TTL = 60 * 60 * 5  # Время жизни кэша 5 часов
 
#! Celery
# from celery.schedules import crontab

# CELERY_BEAT_SCHEDULE = {
#     'check-response-queue-every-minute': {
#         'task': 'mainBot.tasks.check_response_queue',  # Имя задачи
#         'schedule': crontab(minute='*/1'),  # Настройка по расписанию: каждый минуту
#     },
# }

CELERY_TASK_ACKS_LATE = True  # Задачи подтверждаются только после завершения
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,  # Увеличение таймаута до 1 часа
}
#CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_URL = f'amqp://{os.getenv('RABBITMQ_DEFAULT_USER')}:{os.getenv('RABBITMQ_DEFAULT_PASS')}@rabbitmq/'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'



# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'RU-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

BOT_TOKEN = os.getenv("BOT_TOKEN") # токен
WEBHOOK_BASE_URL = os.getenv("BASE_URL")
#CSRF_TRUSTED_ORIGINS=[WEBHOOK_BASE_URL] 
if DEBUG:
    CSRF_COOKIE_SECURE = False

# GEOPOSITION SERVICES:
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY")