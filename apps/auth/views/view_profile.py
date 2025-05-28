# apps/auth/views/view_profile.py
"""
Vistas para la gestión del perfil de usuario.
Incluye vistas para mostrar y actualizar el perfil del usuario.
Requiere que el usuario esté autenticado para acceder a estas vistas.
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView

from apps.auth.forms.form_updateProfile import ProfileUpdateForm
from apps.auth.views.view_auth import CustomLoginRequiredMixin

User = get_user_model()


class ProfileView(CustomLoginRequiredMixin, TemplateView):
  """
  Vista para mostrar el perfil del usuario.
  Requiere que el usuario esté autenticado.
  """
  template_name = 'auth/profile/profile.html'

  def get_context_data(self, **kwargs):
    """Añade el usuario actual al contexto de la plantilla"""
    context = super().get_context_data(**kwargs)
    context['user'] = self.request.user
    return context


class UpdateProfileView(CustomLoginRequiredMixin, UpdateView):
  """
  Vista para actualizar el perfil del usuario.
  Permite modificar la información personal y de contacto.
  """
  model = User
  form_class = ProfileUpdateForm
  template_name = 'auth/profile/update_profile.html'
  success_url = reverse_lazy('auth:view_profile')

  def form_valid(self, form):
    """Procesa el formulario válido y muestra mensaje de éxito"""
    messages.success(
      self.request,
      'Tu perfil ha sido actualizado correctamente.'
    )
    return super().form_valid(form)

  def form_invalid(self, form):
    """Maneja errores en el formulario"""
    messages.error(
      self.request,
      'Por favor, corrige los errores en el formulario.'
    )
    return super().form_invalid(form)

  def get_object(self, queryset=None):
    """Retorna el usuario actual para la edición"""
    return self.request.user
