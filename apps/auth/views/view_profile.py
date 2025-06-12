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
from utils.logger import logger

User = get_user_model()


class ProfileView(CustomLoginRequiredMixin, TemplateView):
  """
  Vista para mostrar el perfil del usuario.
  Requiere que el usuario esté autenticado.
  """
  template_name = 'auth/profile/profile.html'

  def get_context_data(self, **kwargs):
    """Añade el usuario actual y textos al contexto de la plantilla"""
    logger.info('ProfileView', 'Cargando datos de perfil de usuario.')
    try:
      context = super().get_context_data(**kwargs)
      context.update({
        'page_title': 'Mi Perfil',
        'app_name': 'DermaIA',
        'title': 'Perfil de usuario',
        'photo_label': 'Foto de perfil',
        'field_labels': {
          'names': 'Nombres',
          'last_names': 'Apellidos',
          'dni': 'DNI',
          'address': 'Dirección',
          'city': 'Ciudad',
          'phone': 'Teléfono',
          'email': 'Correo'
        },
        'default_messages': {
          'not_specified': 'No especificado',
          'not_specified_f': 'No especificada'
        },
        'update_button_text': 'Actualizar Perfil',
        'user': self.request.user
      })
      logger.success('ProfileView', 'Datos de perfil cargados correctamente.')
      return context
    except Exception as e:
      logger.error('ProfileView', f'Error al cargar datos de perfil: {str(e)}')
      messages.error(self.request, 'No se pudo cargar el perfil. Intente de nuevo.')
      return {}


class UpdateProfileView(CustomLoginRequiredMixin, UpdateView):
  """
  Vista para actualizar el perfil del usuario.
  Permite modificar la información personal y de contacto.
  """
  model = User
  form_class = ProfileUpdateForm
  template_name = 'auth/profile/update_profile.html'
  success_url = reverse_lazy('auth:view_profile')

  def get_context_data(self, **kwargs):
        logger.info('UpdateProfileView', 'Cargando formulario de actualización de perfil.')
        try:
            context = super().get_context_data(**kwargs)
            user = self.get_object()
            # Evitar errores si user es None o AnonymousUser
            if user and hasattr(user, 'first_name'):
                logger.info('UpdateProfileView', (
                    f"Datos actuales del usuario (ANTES de editar): "
                    f"Nombres={getattr(user, 'first_name', '')}, Apellidos={getattr(user, 'last_name', '')}, "
                    f"DNI={getattr(user, 'dni', '')}, Email={getattr(user, 'email', '')}, "
                    f"Dirección={getattr(user, 'address', '')}, Ciudad={getattr(user, 'city', '')}, Tel={getattr(user, 'phone', '')}"
                ))
            context.update({
                'app_name': 'DermaIA',
                'page_title': 'Actualización de perfil',
                'title': 'Actualización de perfil',
                'photo_section': {
                    'title': 'Foto de perfil',
                    'alt_text': 'Foto de perfil',
                    'alt_text_default': 'Foto de perfil predeterminada'
                },
                'form_labels': {
                    'first_name': 'Nombres',
                    'last_name': 'Apellidos',
                    'dni': 'Cédula',
                    'email': 'Correo Electrónico',
                    'address': 'Dirección',
                    'city': 'Ciudad',
                    'phone': 'Teléfono'
                },
                'buttons': {
                    'update': 'Actualizar',
                    'cancel': 'Cancelar'
                }
            })
            logger.success('UpdateProfileView', 'Formulario de actualización de perfil cargado correctamente.')
            return context
        except Exception as e:
            logger.error('UpdateProfileView', f'Error al cargar formulario de perfil: {str(e)}')
            messages.error(self.request, 'No se pudo cargar el formulario de perfil. Intente de nuevo.')
            return {}

  def form_valid(self, form):
        logger.info('UpdateProfileView', 'Intentando actualizar perfil de usuario.')
        try:
            user = self.get_object()
            if user and hasattr(user, 'first_name'):
                logger.success('UpdateProfileView', (
                    f"Datos nuevos del usuario (DESPUÉS de editar): "
                    f"Nombres={form.cleaned_data.get('first_name', '')}, Apellidos={form.cleaned_data.get('last_name', '')}, "
                    f"DNI={form.cleaned_data.get('dni', '')}, Email={form.cleaned_data.get('email', '')}, "
                    f"Dirección={form.cleaned_data.get('address', '')}, Ciudad={form.cleaned_data.get('city', '')}, Tel={form.cleaned_data.get('phone', '')}"
                ))
            response = super().form_valid(form)
            logger.success('UpdateProfileView', 'Perfil actualizado correctamente.')
            messages.success(
                self.request,
                'Tu perfil ha sido actualizado correctamente.'
            )
            return response
        except Exception as e:
            logger.error('UpdateProfileView', f'Error al actualizar perfil: {str(e)}')
            messages.error(self.request, 'No se pudo actualizar el perfil. Intente de nuevo.')
            return super().form_invalid(form)

  def form_invalid(self, form):
    """Maneja errores en el formulario"""
    logger.warning('UpdateProfileView', f'Errores de validación en actualización de perfil: {form.errors}')
    messages.error(
      self.request,
      'Por favor, corrige los errores en el formulario.'
    )
    return super().form_invalid(form)

  def get_object(self, queryset=None):
        """Retorna el usuario actual para la edición"""
        logger.info('UpdateProfileView', 'Obteniendo usuario autenticado para edición de perfil.')
        try:
            user = self.request.user
            nombre = user.get_full_name() if callable(getattr(user, 'get_full_name', None)) else str(user)
            logger.success('UpdateProfileView', f'Usuario obtenido: {nombre}')
            return user
        except Exception as e:
            logger.error('UpdateProfileView', f'Error al obtener usuario: {str(e)}')
            messages.error(self.request, 'No se pudo obtener el usuario. Intente de nuevo.')
            return None
