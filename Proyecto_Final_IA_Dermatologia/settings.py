"""
Django settings for Proyecto_Final_IA_Dermatologia project.
Configuración principal del proyecto Django para el sistema de IA en Dermatología.
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Carga de variables de entorno
load_dotenv()

# Configuración de rutas base
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuración de seguridad
# ADVERTENCIA: Mantener la clave secreta en producción
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-x+hb#da2=lf87z0fol@3pt8hxcm+g=dfc)tzciw7xv!llc3wxl')

# Configuración para Gemini AI
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Configuración de entorno
DEBUG = True

# Configuración de hosts permitidos
ALLOWED_HOSTS = ['*'] if DEBUG else []

# Configuración de aplicaciones
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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
    'utils.session_middleware.SessionTimeoutMiddleware',  # Middleware personalizado para timeout de sesión
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuración de seguridad adicional
# En desarrollo, estas configuraciones están desactivadas
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 año
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
SESSION_COOKIE_AGE = 2700  # 45 minutos en segundos
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True  # Actualiza la cookie en cada petición
SESSION_COOKIE_AGE_REFRESH = True  # Renueva el tiempo de expiración en cada petición - en false no renueva y mandara al login aunque el usuario este usando la web
SESSION_SECURITY_WARN_AFTER = 2400  # Advertencia después de 40 minutos de inactividad
SESSION_SECURITY_EXPIRE_AFTER = 2700  # Expira después de 45 minutos de inactividad

CSRF_TRUSTED_ORIGINS = ['http://localhost:*', 'http://127.0.0.1:*']
CSRF_COOKIE_SECURE = False  # En desarrollo lo dejamos en False
SESSION_COOKIE_SECURE = False  # En desarrollo lo dejamos en False

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
TIME_ZONE = 'America/Guayaquil'  # Zona horaria de Ecuador
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

# Configuración de usuario personalizado y rutas de autenticación
AUTH_USER_MODEL = 'AUTH.User'
PASSWORD_RESET_URL = '/auth/password_reset/'
LOGIN_URL = '/'
LOGOUT_REDIRECT_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/core/home/'

# Campo de clave primaria predeterminado
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
