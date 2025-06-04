# apps/core/views/views.py
"""
Vistas principales de la aplicación core.
Maneja la página de inicio y la página de características del sistema.
Requiere que el usuario esté autenticado para acceder a estas vistas.
"""

from django.views.generic import TemplateView
from django.db.models import QuerySet

from apps.Dermatologia_IA.models import SkinImage
from apps.auth.views.view_auth import CustomLoginRequiredMixin


class HomeView(CustomLoginRequiredMixin, TemplateView):
  """
  Vista de la página principal.
  Muestra la interfaz inicial y resumen del sistema.
  """
  template_name = "core/home/home.html"
  RECENT_IMAGES_LIMIT = 3  # Número de imágenes recientes a mostrar

  def get_context_data(self, **kwargs) -> dict:
    """
    Prepara el contexto para la plantilla principal.
    Incluye textos estáticos y contenido de la página de inicio.

    Returns:
        dict: Contexto con los datos necesarios para renderizar la página de inicio.
    """
    context = super().get_context_data(**kwargs)
    context.update({
      'page_title': 'Inicio',
      'app_name': 'DermaIA',
      'current_page': 'home',
      'hero_section': {
        'title': 'DermaIA: Inteligencia Artificial para Dermatología',
        'subtitle': 'Mejorando el diagnóstico dermatológico con tecnología avanzada',
        'description': ('Sistema inteligente de apoyo al diagnóstico dermatológico que utiliza las '
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
    return context

  def _get_recent_images(self) -> QuerySet[SkinImage]:
    """
    Obtiene las imágenes más recientes del sistema.

    Returns:
        QuerySet[SkinImage]: Las últimas imágenes ordenadas por fecha de subida.
    """
    return SkinImage.objects.order_by('-uploaded_at')[:self.RECENT_IMAGES_LIMIT]


class CharacteristicsView(CustomLoginRequiredMixin, TemplateView):
  """
  Vista de la página de características.
  Muestra información sobre las funcionalidades del sistema.
  """
  template_name = "core/characteristics.html"

  def get_context_data(self, **kwargs) -> dict:
    """
    Prepara el contexto para la plantilla de características.
    Incluye todos los textos y contenido estático.
    """
    context = super().get_context_data(**kwargs)
    context.update({
      'page_title': 'Características',
      'app_name': 'DermaIA',
      'current_page': 'characteristics',
      'main_title': 'Características Principales',
      'main_description': ('Descubre las funcionalidades avanzadas que DermaIA ofrece para mejorar el '
                         'diagnóstico y tratamiento de afecciones dermatológicas con tecnología de '
                         'inteligencia artificial.'),
      'features': [
        {
          'icon': 'fas fa-user-shield',
          'title': 'Gestión de Usuario Segura',
          'description': ('Autenticación robusta y perfiles personalizables para mayor seguridad y '
                         'comodidad. Gestiona tu información médica con total confidencialidad y '
                         'control de acceso.')
        },
        {
          'icon': 'fas fa-cloud-upload-alt',
          'title': 'Carga Fácil de Imágenes',
          'description': ('Sube tus imágenes dermatológicas en diversos formatos con nuestra '
                         'interfaz intuitiva. Compatible con múltiples dispositivos y optimización '
                         'automática de calidad.')
        },
        {
          'icon': 'fas fa-brain',
          'title': 'Análisis IA Avanzado',
          'description': ('Detección precisa de afecciones utilizando algoritmos de aprendizaje '
                         'profundo. Resultados rápidos y confiables para apoyar diagnósticos '
                         'médicos profesionales.')
        },
        {
          'icon': 'fas fa-chart-line',
          'title': 'Reportes Detallados',
          'description': ('Genera reportes completos con análisis visual, recomendaciones y '
                         'seguimiento. Exporta resultados en múltiples formatos para compartir con '
                         'profesionales.')
        },
        {
          'icon': 'fas fa-history',
          'title': 'Historial Médico',
          'description': ('Mantén un registro completo de todos los análisis y evolución del '
                         'paciente. Acceso rápido al historial para seguimiento y comparativas '
                         'temporales.')
        }
      ]
    })
    return context
