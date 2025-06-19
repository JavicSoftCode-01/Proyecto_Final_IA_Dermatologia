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
  path('home/', HomeView.as_view(), name='home'),
  path('characteristics/', CharacteristicsView.as_view(), name='characteristics'),
]
