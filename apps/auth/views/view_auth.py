"""
Vistas de autenticación para la aplicación auth.
Incluye registro, inicio de sesión, cierre de sesión y restablecimiento de contraseña.
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
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
from utils.logger import logger

User = get_user_model()


class CustomLoginRequiredMixin(LoginRequiredMixin):
  """
  Mixin personalizado para requerir autenticación.
  Añade mensajes de error cuando se requiere inicio de sesión.
  """

  login_url = settings.LOGIN_URL
  redirect_field_name = 'next'

  def handle_no_permission(self, request=None):
    if request is None:
      request = getattr(self, 'request', None)
    if request is not None:
      messages.error(request, "Iniciar sesión para acceder.")
    return super().handle_no_permission()


class RegisterUserView(FormView):
  """Vista para el registro de nuevos usuarios"""

  template_name = 'auth/register.html'
  form_class = CustomUserCreationForm
  success_url = reverse_lazy('auth:login')

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'page_title': 'Registro',
      'app_name': 'DermaIA',
      'subtitle': 'Ingrese sus datos del formulario para registrarse en el sistema',
      'first_name_label': 'Nombres',
      'first_name_placeholder': 'Ingrese sus nombres',
      'last_name_label': 'Apellidos',
      'last_name_placeholder': 'Ingrese sus apellidos',
      'email_label': 'Correo Electrónico',
      'email_placeholder': 'Ingrese su correo electrónico',
      'password_label': 'Contraseña',
      'password_placeholder': 'Ingrese su contraseña',
      'confirm_password_label': 'Confirmar Contraseña',
      'confirm_password_placeholder': 'Confirme su contraseña',
      'register_button_text': 'Registrarse',
      'login_text': '¿Ya tienes cuenta?',
      'login_link_text': 'Inicia sesión'
    })
    return context

  def form_valid(self, form):
    logger.info('RegisterUserView', 'Intentando registrar nuevo usuario.')
    try:
      user = form.save()
      self._show_success_message(user)
      logger.success('RegisterUserView', f'Usuario registrado exitosamente: {user.get_full_name()}')
      return super().form_valid(form)
    except Exception as e:
      logger.error('RegisterUserView', f'Error al registrar usuario: {str(e)}')
      messages.error(self.request, 'No se pudo completar el registro. Por favor intente de nuevo.')
      return super().form_invalid(form)

  def form_invalid(self, form):
    self._log_registration_errors(form)
    messages.error(self.request, "Por favor, corrija los errores en el formulario.")
    return super().form_invalid(form)

  def _log_registration_errors(self, form):
    logger.warning('RegisterUserView', f'Errores de validación en registro: {form.errors}')

  def _show_success_message(self, user):
    messages.success(
      self.request,
      f'¡Registro exitoso Dr. {user.get_full_name()}! Por favor inicie sesión con sus credenciales.'
    )


class LoginUserView(FormView):
  """Vista para el inicio de sesión de usuarios"""

  template_name = 'auth/login.html'
  form_class = CustomAuthenticationForm
  success_url = reverse_lazy('core:home')

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'page_title': 'Iniciar Sesión',
      'app_name': 'DermaIA',
      'subtitle': 'Ingrese sus credenciales para acceder al sistema',
      'email_label': 'Correo Electrónico',
      'password_label': 'Contraseña',
      'forgot_password_text': '¿Olvidó su contraseña?',
      'login_button_text': 'Iniciar Sesión',
      'register_text': '¿No tiene una cuenta?',
      'register_link_text': 'Regístrese'
    })
    return context

  def form_valid(self, form):
    logger.info('LoginUserView', 'Intentando iniciar sesión.')
    try:
      user = form.get_user()
      if user is not None:
        return self._handle_successful_login(user)
      return self._handle_failed_login()
    except Exception as e:
      logger.error('LoginUserView', f'Error en inicio de sesión: {str(e)}')
      messages.error(self.request, 'No se pudo iniciar sesión. Intente de nuevo.')
      return self.form_invalid(form)

  def form_invalid(self, form):
    messages.error(self.request, "Por favor, corrija los errores en el formulario.")
    return super().form_invalid(form)

  def _handle_successful_login(self, user):
    login(self.request, user)
    logger.success('LoginUserView', f'Login exitoso para usuario: {user.get_full_name()}')
    messages.success(
      self.request,
      f'¡Bienvenido Dr. {user.get_full_name()}!'
    )
    return redirect(self.request.GET.get('next') or 'core:home')

  def _handle_failed_login(self):
    logger.warning('LoginUserView', 'Intento de login fallido.')
    messages.error(
      self.request,
      "Credenciales inválidas. Por favor, verifique su correo y contraseña."
    )
    return self.form_invalid(None)


class LogoutUserView(View):
  """Vista para cerrar sesión de usuarios"""

  def get(self, request):
    logger.info('LogoutUserView', 'Intentando cerrar sesión.')
    try:
      user_name = request.user.get_full_name()
      logout(request)
      logger.success('LogoutUserView', f'Sesión cerrada correctamente para: {user_name}')
      messages.success(
        request,
        f'Sesión cerrada correctamente. ¡Hasta luego Dr. {user_name}!'
      )
      return redirect('auth:login')
    except Exception as e:
      logger.error('LogoutUserView', f'Error al cerrar sesión: {str(e)}')
      messages.error(request, 'No se pudo cerrar la sesión. Intente de nuevo.')
      return redirect('core:home')


class PasswordResetRequestView(FormView):
  """Vista para solicitar el restablecimiento de contraseña"""

  template_name = 'auth/reset_password/password_reset.html'
  form_class = PasswordResetForm

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'page_title': 'Restablecer Contraseña',
      'app_name': 'DermaIA',
    })
    return context

  def form_valid(self, form):
    logger.info('PasswordResetRequestView', 'Solicitud de restablecimiento de contraseña iniciada.')
    email = form.cleaned_data['email']
    try:
      users = User.objects.filter(email=email)
      if not users.exists():
        logger.warning('PasswordResetRequestView', f'No existe usuario con el email: {email}')
        messages.warning(self.request, 'No existe usuario registrado con ese correo.')
        return super().form_invalid(form)
      for user in users:
        try:
          context = self._get_email_context(user)
          subject = 'Restablecimiento de contraseña en DermaIA'
          email_body = render_to_string('auth/reset_password/email_resetPS/password_reset_email.html', context)
          email_message = EmailMultiAlternatives(
            subject,
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
          )
          email_message.attach_alternative(email_body, "text/html")
          email_message.send()
          logger.success('PasswordResetRequestView', f'Correo de restablecimiento enviado a: {user.email}')
        except Exception as e:
          logger.error('PasswordResetRequestView', f'Error enviando correo: {str(e)}')
          messages.error(self.request,
                         'No se pudo enviar el correo de restablecimiento. Verifique que su correo esté registrado y vuelva a intentarlo.')
          return super().form_invalid(form)
      messages.success(self.request,
                       'Si el correo está registrado, se ha enviado un email con instrucciones para restablecer su contraseña.')
      # Redirige correctamente usando reverse_lazy
      from django.urls import reverse
      return redirect(reverse('auth:login'))
    except Exception as e:
      logger.error('PasswordResetRequestView', f'Error al solicitar restablecimiento: {str(e)}')
      messages.error(self.request, 'No se pudo procesar la solicitud. Intente más tarde.')
      from django.urls import reverse
      return redirect(reverse('auth:login'))

  def _send_reset_email(self, user):
    try:
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
      logger.success('PasswordResetRequestView', f'Correo enviado correctamente a: {user.email}')
    except Exception as e:
      logger.error('PasswordResetRequestView', f'Error enviando correo: {str(e)}')
      raise

  def _get_email_context(self, user):
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

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'page_title': 'Cambiar Contraseña',
      'app_name': 'DermaIA',
      'title': 'Establecer una nueva contraseña',
      'subtitle': 'Crea una nueva contraseña. Asegúrate de que sea diferente a las anteriores por seguridad.',
      'new_password_label': 'Nueva contraseña',
      'new_password_placeholder': 'Ingrese su nueva contraseña',
      'confirm_password_label': 'Confirmar nueva contraseña',
      'confirm_password_placeholder': 'Confirme su nueva contraseña',
      'submit_button_text': 'Actualizar contraseña'
    })
    return context

  def form_valid(self, form):
    logger.info('CustomPasswordResetConfirmView', 'Intentando actualizar contraseña.')
    try:
      response = super().form_valid(form)
      logger.success('CustomPasswordResetConfirmView', 'Contraseña actualizada correctamente.')
      messages.success(
        self.request,
        "Tu contraseña ha sido actualizada correctamente."
      )
      return response
    except Exception as e:
      logger.error('CustomPasswordResetConfirmView', f'Error al actualizar contraseña: {str(e)}')
      messages.error(self.request, 'No se pudo actualizar la contraseña. Intente de nuevo.')
      return super().form_invalid(form)
