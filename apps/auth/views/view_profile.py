# apps/auth/views/view_profile.py
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView

from apps.auth.forms.form_updateProfile import ProfileUpdateForm
from apps.auth.models import User
from apps.auth.views.view_auth import CustomLoginRequiredMixin

User = get_user_model()


class ViewProfileView(CustomLoginRequiredMixin, TemplateView):
  template_name = 'auth/profile/profile.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['user'] = self.request.user
    return context


class UpdateProfileView(CustomLoginRequiredMixin, UpdateView):
  model = User
  form_class = ProfileUpdateForm
  template_name = 'auth/profile/update_profile.html'
  success_url = reverse_lazy('auth:view_profile')

  def form_valid(self, form):
    messages.success(self.request, 'Tu perfil ha sido actualizado correctamente.')
    return super().form_valid(form)

  def form_invalid(self, form):
    messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
    return super().form_invalid(form)

  def get_object(self, queryset=None):
    return User.objects.get(pk=self.request.user.pk)
