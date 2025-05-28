# apps/auth/views/view_auth.py
"""
Vistas de autenticación para la aplicación auth.
Incluye registro, inicio de sesión, cierre de sesión y restablecimiento de contraseña.
"""

from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views import View
from django.views.generic.edit import FormView

from apps.auth.forms.form_auth import (
  CustomAuthenticationForm,
  CustomSetPasswordForm,
  CustomUserCreationForm
)

User = get_user_model()


class CustomLoginRequiredMixin(LoginRequiredMixin):
  """
  Mixin personalizado para requerir autenticación.
  Añade mensajes de error cuando se requiere inicio de sesión.
  """
  login_url = settings.LOGIN_URL
  redirect_field_name = 'next'

  def handle_no_permission(self, request=None):
    """Maneja el caso cuando el usuario no tiene permiso para acceder"""
    request = request or self.request
    messages.error(request, "Iniciar sesión para acceder.")
    return super().handle_no_permission()


class RegisterUserView(FormView):
  """Vista para el registro de nuevos usuarios"""
  template_name = 'auth/register.html'
  form_class = CustomUserCreationForm
  success_url = reverse_lazy('auth:login')

  def form_valid(self, form):
    """Procesa el formulario válido y registra al usuario"""
    user = form.save()
    self._show_success_message(user)
    return super().form_valid(form)

  def form_invalid(self, form):
    """Maneja errores en el formulario"""
    self._log_registration_errors(form)
    messages.error(self.request, "Por favor, corrija los errores en el formulario.")
    return super().form_invalid(form)

  def dispatch(self, request, *args, **kwargs):
    """Redirige usuarios autenticados a la página principal"""
    if request.user.is_authenticated:
      return redirect('core:home')
    return super().dispatch(request, *args, **kwargs)

  def _show_success_message(self, user):
    """Muestra mensaje de éxito al registrar usuario"""
    messages.success(
      self.request,
      f'¡Registro exitoso Dr. {user.first_name} {user.last_name}! '
      'Por favor inicie sesión con sus credenciales.'
    )

  def _log_registration_errors(self, form):
    """Registra errores de registro para depuración"""
    print("=== ERRORES DE REGISTRO ===")
    print(form.errors)
    print("===========================")


class LoginUserView(FormView):
  """Vista para el inicio de sesión de usuarios"""
  template_name = 'auth/login.html'
  form_class = CustomAuthenticationForm
  success_url = reverse_lazy('core:home')

  def form_valid(self, form):
    """Procesa el inicio de sesión exitoso"""
    user = form.get_user()
    if user is not None:
      return self._handle_successful_login(user)
    return self._handle_failed_login()

  def form_invalid(self, form):
    """Maneja errores en el formulario de login"""
    messages.error(self.request, "Por favor, corrija los errores en el formulario.")
    return super().form_invalid(form)

  def dispatch(self, request, *args, **kwargs):
    """Redirige usuarios ya autenticados"""
    if request.user.is_authenticated:
      return redirect('core:home')
    return super().dispatch(request, *args, **kwargs)

  def _handle_successful_login(self, user):
    """Procesa el login exitoso y redirige apropiadamente"""
    login(self.request, user)
    messages.success(
      self.request,
      f'¡Bienvenido Dr. {user.first_name} {user.last_name}!'
    )
    return redirect(self.request.GET.get('next') or 'core:home')

  def _handle_failed_login(self):
    """Maneja el caso de login fallido"""
    messages.error(
      self.request,
      "Credenciales inválidas. Por favor, verifique su correo y contraseña."
    )
    return self.form_invalid(None)


class LogoutUserView(View):
  """Vista para cerrar sesión de usuarios"""

  def get(self, request):
    """Procesa la solicitud de cierre de sesión"""
    user_name = f"{request.user.first_name} {request.user.last_name}"
    logout(request)
    messages.success(
      request,
      f'Sesión cerrada correctamente. ¡Hasta luego Dr. {user_name}!'
    )
    return redirect('auth:login')


class PasswordResetRequestView(FormView):
  """Vista para solicitar el restablecimiento de contraseña"""
  template_name = 'auth/reset_password/password_reset.html'
  form_class = PasswordResetForm

  def form_valid(self, form):
    """Procesa la solicitud de restablecimiento de contraseña"""
    email = form.cleaned_data['email']
    users = User.objects.filter(email=email)

    if users.exists():
      self._send_reset_email(users.first())
      messages.success(
        self.request,
        "Se ha enviado un correo con las instrucciones para restablecer tu contraseña."
      )
    return redirect("auth:login")

  def _send_reset_email(self, user):
    """Envía el correo de restablecimiento de contraseña"""
    context = self._get_email_context(user)
    email_content = render_to_string(
      "auth/reset_password/password_reset_email.html",
      context
    )

    email = EmailMultiAlternatives(
      "Restablecimiento de contraseña - DermaIA",
      email_content,
      settings.DEFAULT_FROM_EMAIL,
      [user.email]
    )
    email.attach_alternative(email_content, "text/html")
    email.send()

  def _get_email_context(self, user):
    """Prepara el contexto para la plantilla del correo"""
    return {
      "email": user.email,
      "domain": self.request.get_host(),
      "site_name": "DermaIA",
      "uid": urlsafe_base64_encode(force_bytes(user.pk)),
      "user": user,
      "token": default_token_generator.make_token(user),
      "protocol": "https" if self.request.is_secure() else "http"
    }


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
  """Vista para confirmar el restablecimiento de contraseña"""
  form_class = CustomSetPasswordForm
  template_name = 'auth/reset_password/password_reset_confirm.html'
  success_url = reverse_lazy('auth:password_reset_complete')

  def form_valid(self, form):
    """Procesa el formulario válido de cambio de contraseña"""
    messages.success(
      self.request,
      "Tu contraseña ha sido actualizada correctamente."
    )
    return super().form_valid(form)
