from pathlib import Path
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────
# Security
# ─────────────────────────────────────────────────────────────

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-xydf()ksfsmc06z*z6g0n%gus_1ir9hc=dj9!o$-33te23!5b1'
)

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'school-app-production-2e35.up.railway.app',
    'localhost',
    '127.0.0.1',
    'testserver',
]

CSRF_TRUSTED_ORIGINS = [
    'https://school-app-production-2e35.up.railway.app',
]

# ─────────────────────────────────────────────────────────────
# Installed Apps
# ─────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',

    # Local apps
    'accounts',
]

# ─────────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────────

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # WhiteNoise
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',

    # CORS
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

# ─────────────────────────────────────────────────────────────
# Templates
# ─────────────────────────────────────────────────────────────

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# ─────────────────────────────────────────────────────────────
# Custom User Model
# ─────────────────────────────────────────────────────────────

AUTH_USER_MODEL = 'accounts.User'

# ─────────────────────────────────────────────────────────────
# Database (Railway PostgreSQL)
# ─────────────────────────────────────────────────────────────

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'railway',
        'USER': 'postgres',
        'PASSWORD': 'IfcorwoLvejrdHTgUDAFMmZTozaihMml',
        'HOST': 'postgres.railway.internal',
        'PORT': '5432',
    }
}

# ─────────────────────────────────────────────────────────────
# Password Validation
# ─────────────────────────────────────────────────────────────

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

# ─────────────────────────────────────────────────────────────
# Internationalization
# ─────────────────────────────────────────────────────────────

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# ─────────────────────────────────────────────────────────────
# Static Files
# ─────────────────────────────────────────────────────────────

STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = (
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
)

# ─────────────────────────────────────────────────────────────
# Default Primary Key Field Type
# ─────────────────────────────────────────────────────────────

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────────────────────
# Django REST Framework
# ─────────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),

    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],

    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/min',
        'user': '100/min',
    },
}

# ─────────────────────────────────────────────────────────────
# Simple JWT
# ─────────────────────────────────────────────────────────────

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),

    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    'ROTATE_REFRESH_TOKENS': True,

    'BLACKLIST_AFTER_ROTATION': True,

    'ALGORITHM': 'HS256',

    'SIGNING_KEY': SECRET_KEY,

    'AUTH_HEADER_TYPES': ('Bearer',),

    'USER_ID_FIELD': 'id',

    'USER_ID_CLAIM': 'user_id',

    'TOKEN_OBTAIN_SERIALIZER':
        'accounts.serializers.CustomTokenObtainPairSerializer',
}

# ─────────────────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────────────────

CORS_ALLOW_ALL_ORIGINS = True

# ─────────────────────────────────────────────────────────────
# Security Headers (Production Recommended)
# ─────────────────────────────────────────────────────────────

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = True

CSRF_COOKIE_SECURE = True
