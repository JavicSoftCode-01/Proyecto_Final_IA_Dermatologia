"""
Vistas principales de la aplicación core.
Maneja la página de inicio y la página de características del sistema.
Requiere que el usuario esté autenticado para acceder a estas vistas.
"""

from django.db.models import QuerySet
from django.views.generic import TemplateView

from apps.Dermatologia_IA.models import SkinImage
from apps.auth.views.view_auth import CustomLoginRequiredMixin
from utils.logger import logger


class HomeView(CustomLoginRequiredMixin, TemplateView):
  """
  Vista de la página principal.
  Muestra la interfaz inicial y resumen del sistema.
  """

  template_name = "core/home/home.html"
  RECENT_IMAGES_LIMIT = 3

  def get_context_data(self, **kwargs) -> dict:
    logger.info('HomeView', 'Preparando contexto para la página de inicio.')
    try:
      context = super().get_context_data(**kwargs)
      context.update({
        'page_title': 'Inicio',
        'app_name': 'DermaIA',
        'current_page': 'home',
        'hero_section': {
          'title': 'DermaIA: Inteligencia Artificial para Dermatología',
          'subtitle': 'Mejorando el diagnóstico dermatológico con tecnología avanzada',
          'description': (
            'Sistema inteligente de apoyo al diagnóstico dermatológico que utiliza las '
            'últimas tecnologías en inteligencia artificial para analizar imágenes y ayudar a '
            'identificar afecciones de la piel.'),
        },
        'benefits': [
          {
            'icon': 'fas fa-check-circle',
            'title': 'Diagnóstico Rápido',
            'description': 'Obtén resultados preliminares en minutos usando nuestro sistema de IA'
          },
          {
            'icon': 'fas fa-shield-alt',
            'title': 'Alta Precisión',
            'description': 'Análisis basado en modelos entrenados con miles de casos clínicos'
          },
          {
            'icon': 'fas fa-user-md',
            'title': 'Apoyo Profesional',
            'description': 'Herramienta de soporte para profesionales de la salud'
          }
        ],
        'action_button': {
          'text': 'Comenzar Análisis',
          'url': '/upload'
        },
        'recent_images': self._get_recent_images()
      })
      logger.success('HomeView', 'Contexto de página de inicio preparado correctamente.')
      return context
    except Exception as e:
      logger.error('HomeView', f'Error al preparar contexto de inicio: {str(e)}')
      return {
        'page_title': 'Inicio',
        'app_name': 'DermaIA',
        'current_page': 'home',
        'hero_section': {},
        'benefits': [],
        'action_button': {},
        'recent_images': []
      }

  def _get_recent_images(self) -> QuerySet:
    logger.info('HomeView', 'Obteniendo imágenes recientes.')
    try:
      images = SkinImage.objects.order_by('-uploaded_at')[:self.RECENT_IMAGES_LIMIT]
      logger.success('HomeView', f'Se obtuvieron {len(images)} imágenes recientes.')
      return images
    except Exception as e:
      logger.error('HomeView', f'Error al obtener imágenes recientes: {str(e)}')
      return SkinImage.objects.none()


class CharacteristicsView(CustomLoginRequiredMixin, TemplateView):
  """
  Vista de la página de características.
  Muestra información sobre las funcionalidades del sistema.
  """

  template_name = "core/characteristics.html"

  def get_context_data(self, **kwargs) -> dict:
    logger.info('CharacteristicsView', 'Preparando contexto para la página de características.')
    try:
      context = super().get_context_data(**kwargs)
      context.update({
        'page_title': 'Características',
        'app_name': 'DermaIA',
        'current_page': 'characteristics',
        'main_title': 'Características Principales',
        'main_description': (
          'Descubre las funcionalidades avanzadas que DermaIA ofrece para mejorar el '
          'diagnóstico y tratamiento de afecciones dermatológicas con tecnología de '
          'inteligencia artificial.'),
        'features': [
          {
            'icon': 'fas fa-user-shield',
            'title': 'Gestión de Usuario Segura',
            'description': (
              'Autenticación robusta y perfiles personalizables para mayor seguridad y '
              'comodidad. Gestiona tu información médica con total confidencialidad y '
              'control de acceso.')
          },
          {
            'icon': 'fas fa-cloud-upload-alt',
            'title': 'Carga Fácil de Imágenes',
            'description': (
              'Sube tus imágenes dermatológicas en diversos formatos con nuestra '
              'interfaz intuitiva. Compatible con múltiples dispositivos y optimización '
              'automática de calidad.')
          },
          {
            'icon': 'fas fa-brain',
            'title': 'Análisis IA Avanzado',
            'description': (
              'Detección precisa de afecciones utilizando algoritmos de aprendizaje '
              'profundo. Resultados rápidos y confiables para apoyar diagnósticos '
              'médicos profesionales.')
          },
          {
            'icon': 'fas fa-chart-line',
            'title': 'Reportes Detallados',
            'description': (
              'Genera reportes completos con análisis visual, recomendaciones y '
              'seguimiento. Exporta resultados en múltiples formatos para compartir con '
              'profesionales.')
          },
        ]
      })
      logger.success('CharacteristicsView', 'Contexto de características preparado correctamente.')
      return context
    except Exception as e:
      logger.error('CharacteristicsView', f'Error al preparar contexto de características: {str(e)}')
      return {
        'page_title': 'Características',
        'app_name': 'DermaIA',
        'current_page': 'characteristics',
        'main_title': '',
        'main_description': '',
        'features': []
      }
