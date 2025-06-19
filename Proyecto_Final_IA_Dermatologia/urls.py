"""
Configuración de URLs de Django
Este archivo contiene los patrones de URL para el proyecto Django.
Incluye rutas para la aplicación principal, la aplicación de dermatología, la aplicación central y la interfaz de administración.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
                path('admin/', admin.site.urls),
                path('', include('apps.auth.urls')),
                path('core/', include('apps.core.urls')),
                path('dermatology/', include('apps.Dermatologia_IA.urls')),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
