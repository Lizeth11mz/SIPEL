import os
from pathlib import Path
from cryptography.fernet import Fernet # Importante para generar la clave

# ==========================================================
# BASE DIR
# ==========================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================================
# SECURITY
# ==========================================================
SECRET_KEY = 'django-insecure-z*5-1p*s' 
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Clave para cifrado a nivel de aplicación (Fernet)
# Esta clave es vital; no la compartas ni la pierdas, 
# o no podrás descifrar los datos que cifres con ella.
FERNET_KEY = b'G0-8g3_qJ8eP4Z_9Z4S8_K_X9W-yJt4Z8hJpY7fM_j4='

# ==========================================================
# APPS
# ==========================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'core',
    'inventario',
    'admin_sistema',
]

# ==========================================================
# MIDDLEWARE
# ==========================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sma_inventario.urls'

# ==========================================================
# TEMPLATE SETTINGS
# ==========================================================
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
            ],
        },
    },
]

WSGI_APPLICATION = 'sma_inventario.wsgi.application'

# ==========================================================
# DATABASE
# ==========================================================
DATABASES = {
    'default': {
        'ENGINE': 'mssql', 
        'NAME': 'Educacion',
        'HOST': 'LIZET-020211\\SQLSERVER',
        'PORT': '',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'extra_params': 'Trusted_Connection=yes;TrustServerCertificate=yes',
        },
    },
}

# ==========================================================
# AUTHENTICATION
# ==========================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# ==========================================================
# STATIC & MEDIA
# ==========================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# ==========================================================
# LOGIN CONFIGURATION
# ==========================================================
LOGIN_REDIRECT_URL = 'core:bienvenido' 
LOGIN_URL = 'core:login'
LOGOUT_REDIRECT_URL = 'core:index' 


AUTHENTICATION_BACKENDS = [
    'inventario.backends.BinaryPasswordBackend',
    'django.contrib.auth.backends.ModelBackend',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'