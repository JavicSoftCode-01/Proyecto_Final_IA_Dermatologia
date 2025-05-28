# apps\core\urls.py
"""
Configuración de URLs para el módulo core.
Incluye rutas para la página principal y características del sistema.
"""

from django.urls import path

from apps.core.views.views import (
  HomeView,
  CharacteristicsView
)

app_name = 'core'

urlpatterns = [
  # URLs para vistas principales del sistema
  path('home/', HomeView.as_view(), name='home'),

  # URLs para información y características
  path('characteristics/', CharacteristicsView.as_view(), name='characteristics'),
]
