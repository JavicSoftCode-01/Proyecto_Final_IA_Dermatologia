"""
Django settings for Proyecto_Final_IA_Dermatologia project.
Configuración principal del proyecto Django para el sistema de IA en Dermatología.
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-x+hb#da2=lf87z0fol@3pt8hxcm+g=dfc)tzciw7xv!llc3wxl')

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

DEBUG = True

ALLOWED_HOSTS = ['*'] if DEBUG else []

# Configuración de aplicaciones
INSTALLED_APPS = [
  'django.contrib.admin',
  'django.contrib.auth',
  'django.contrib.contenttypes',
  'django.contrib.sessions',
  'django.contrib.messages',
  'django.contrib.staticfiles',

  'storages',
  'apps.Dermatologia_IA.apps.DermatologiaIaConfig',
  'apps.core.apps.CoreConfig',
  'apps.auth.apps.AuthConfig',
]

# Configuración de middleware
MIDDLEWARE = [
  'django.middleware.security.SecurityMiddleware',
  'django.contrib.sessions.middleware.SessionMiddleware',
  'django.middleware.common.CommonMiddleware',
  'django.middleware.csrf.CsrfViewMiddleware',
  'django.contrib.auth.middleware.AuthenticationMiddleware',
  'utils.session_middleware.SessionTimeoutMiddleware',
  'django.contrib.messages.middleware.MessageMiddleware',
  'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuración de seguridad
if not DEBUG:
  SECURE_SSL_REDIRECT = True
  SECURE_HSTS_SECONDS = 31536000
  SECURE_HSTS_INCLUDE_SUBDOMAINS = True
  SECURE_HSTS_PRELOAD = True
  SECURE_BROWSER_XSS_FILTER = True
  SECURE_CONTENT_TYPE_NOSNIFF = True
  X_FRAME_OPTIONS = 'DENY'
  CSRF_COOKIE_SECURE = True
  SESSION_COOKIE_SECURE = True
else:
  SECURE_SSL_REDIRECT = False
  CSRF_COOKIE_SECURE = False
  SESSION_COOKIE_SECURE = False

# Configuración de sesión y CSRF
SESSION_COOKIE_AGE = 2700
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_AGE_REFRESH = True
SESSION_SECURITY_WARN_AFTER = 2400
SESSION_SECURITY_EXPIRE_AFTER = 2700

CSRF_TRUSTED_ORIGINS = ['http://localhost:*', 'http://127.0.0.1:*']
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# URLs y templates
ROOT_URLCONF = 'Proyecto_Final_IA_Dermatologia.urls'

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

WSGI_APPLICATION = 'Proyecto_Final_IA_Dermatologia.wsgi.application'

# Configuración de base de datos
DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.getenv('DB_NAME'),
    'USER': os.getenv('DB_USER'),
    'PASSWORD': os.getenv('DB_PASSWORD'),
    'HOST': os.getenv('DB_HOST'),
    'PORT': os.getenv('DB_PORT'),
  }
}

# Validación de contraseñas
AUTH_PASSWORD_VALIDATORS = [
  {
    'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
  },
  {
    'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    'OPTIONS': {
      'min_length': 8,
    }
  },
  {
    'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
  },
  {
    'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
  },
]

# Configuración de autenticación
AUTHENTICATION_BACKENDS = [
  'django.contrib.auth.backends.ModelBackend',
]

# Configuración de zona horaria y lenguaje
LANGUAGE_CODE = 'es-EC'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True

# Configuración de correo electrónico
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

# Archivos estáticos y media
STATIC_URL = 'static/'
STATICFILES_DIRS = [
  BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuración de Amazon S3
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', 'dermaia')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')

# Configuración de usuario personalizado y rutas de autenticación
AUTH_USER_MODEL = 'AUTH.User'
PASSWORD_RESET_URL = '/auth/password_reset/'
LOGIN_URL = '/'
LOGOUT_REDIRECT_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/core/home/'

# Campo de clave primaria predeterminado
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
