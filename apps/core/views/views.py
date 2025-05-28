# core/views/views.py
from django.views.generic import TemplateView

from apps.Dermatologia_IA.models import SkinImage
from apps.auth.views.view_auth import CustomLoginRequiredMixin


class HomeView(CustomLoginRequiredMixin, TemplateView):
  template_name = "core/home/home.html"

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    # Trae los 3 últimos por fecha de subida
    context['recent_images'] = SkinImage.objects.order_by('-uploaded_at')[:3]
    return context


class CharacteristicsView(CustomLoginRequiredMixin, TemplateView):
  template_name = "core/characteristics.html"

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['current_page'] = 'characteristics'
    return context
