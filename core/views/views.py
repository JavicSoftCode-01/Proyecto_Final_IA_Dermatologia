# core/views/views.py
from django.views.generic import TemplateView

from core.Dermatologia_IA.models import SkinImage


class HomeView(TemplateView):
  template_name = "home/home.html"

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    # Trae los 3 últimos por fecha de subida
    context['recent_images'] = SkinImage.objects.order_by('-uploaded_at')[:3]
    return context
