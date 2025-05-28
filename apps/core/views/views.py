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
  Muestra un dashboard con las imágenes más recientes analizadas por el sistema.
  """
  template_name = "core/home/home.html"
  RECENT_IMAGES_LIMIT = 3  # Número de imágenes recientes a mostrar

  def get_context_data(self, **kwargs) -> dict:
    """
    Prepara el contexto para la plantilla, incluyendo las imágenes más recientes.

    Returns:
        dict: Contexto con las imágenes más recientes ordenadas por fecha.
    """
    context = super().get_context_data(**kwargs)
    context['recent_images'] = self._get_recent_images()
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

    Returns:
        dict: Contexto con la página actual marcada como 'characteristics'.
    """
    context = super().get_context_data(**kwargs)
    context['current_page'] = 'characteristics'
    return context
