# apps/auth/views/view_auth.py

from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout
from django.contrib.auth.forms import PasswordResetForm
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

from apps.auth.forms.form_auth import CustomAuthenticationForm, CustomSetPasswordForm
from apps.auth.forms.form_auth import CustomUserCreationForm

User = get_user_model()

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.conf import settings


class CustomLoginRequiredMixin(LoginRequiredMixin):
  """
  Requiere que el usuario esté autenticado; si no,
  añade un mensaje y redirige a LOGIN_URL.
  """
  login_url = settings.LOGIN_URL
  redirect_field_name = 'next'

  def handle_no_permission(self):
    messages.error(self.request, "Iniciar sesión para acceder.")
    return super().handle_no_permission()


class RegisterUserView(FormView):
  """
  Vista para el registro de nuevos usuarios
  """
  template_name = 'auth/register.html'
  form_class = CustomUserCreationForm
  success_url = reverse_lazy('auth:login')

  def form_valid(self, form):
    user = form.save()
    messages.success(
      self.request,
      f'¡Registro exitoso Dr. {user.first_name} {user.last_name}! Por favor inicie sesión con sus credenciales.'
    )
    return super().form_valid(form)

  def form_invalid(self, form):
    # --- LÍNEA DE DEPURACIÓN CLAVE ---
    print("=== ERRORES DE REGISTRO ===")
    print(form.errors)
    print("===========================")
    # --- FIN LÍNEA DE DEPURACIÓN ---

    messages.error(
      self.request,
      "Por favor, corrija los errores en el formulario."
    )
    return super().form_invalid(form)

  def dispatch(self, request, *args, **kwargs):
    if request.user.is_authenticated:
      return redirect('core:home')
    return super().dispatch(request, *args, **kwargs)


class LoginUserView(FormView):
  """
  Vista para el inicio de sesión
  """
  template_name = 'auth/login.html'
  form_class = CustomAuthenticationForm
  success_url = reverse_lazy('core:home')

  def form_valid(self, form):
    user = form.get_user()

    if user is not None:
      login(self.request, user)
      print("Login successful")

      messages.success(
        self.request,
        f'¡Bienvenido Dr. {user.first_name} {user.last_name}!'
      )

      next_page = self.request.GET.get('next')
      if next_page:
        return redirect(next_page)
      else:
        return redirect('core:home')
    else:
      # Este bloque es un fallback, el error ya debería haber sido manejado por form.clean()
      print("Authentication failed in form_valid - this should not happen if form.is_valid() is True")
      messages.error(
        self.request,
        "Credenciales inválidas. Por favor, verifique su correo y contraseña."
      )
      return self.form_invalid(form)

  def form_invalid(self, form):
    messages.error(
      self.request,
      "Por favor, corrija los errores en el formulario."
    )
    return super().form_invalid(form)

  def dispatch(self, request, *args, **kwargs):
    if request.user.is_authenticated:
      return redirect('core:home')
    return super().dispatch(request, *args, **kwargs)


class LogoutUserView(View):
  """
  Vista para cerrar sesión
  """

  def get(self, request):
    user_name = f"{request.user.first_name} {request.user.last_name}"
    logout(request)
    messages.success(request, f'Sesión cerrada correctamente. ¡Hasta luego Dr. {user_name}!')
    return redirect('auth:login')


class PasswordResetRequestView(FormView):
  """
  Vista para solicitar el restablecimiento de contraseña
  """
  template_name = 'auth/reset_password/password_reset.html'
  form_class = PasswordResetForm

  def form_valid(self, form):
    email = form.cleaned_data['email']
    associated_users = User.objects.filter(email=email)
    if associated_users.exists():
      for user in associated_users:
        subject = "Restablecimiento de contraseña - DermaIA"
        email_template_name = "auth/reset_password/password_reset_email.html"
        context = {
          "email": user.email,
          "domain": self.request.get_host(),
          "site_name": "DermaIA",
          "uid": urlsafe_base64_encode(force_bytes(user.pk)),
          "user": user,
          "token": default_token_generator.make_token(user),
          "protocol": "https" if self.request.is_secure() else "http",
        }
        email_content = render_to_string(email_template_name, context)
        email = EmailMultiAlternatives(
          subject,
          email_content,
          settings.DEFAULT_FROM_EMAIL,
          [user.email],
        )
        email.attach_alternative(email_content, "text/html")
        email.send()
      messages.success(self.request, "Se ha enviado un correo con las instrucciones para restablecer tu contraseña.")
    return redirect("auth:login")


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
  """
  Vista para confirmar el restablecimiento de contraseña
  """
  form_class = CustomSetPasswordForm
  template_name = 'auth/reset_password/password_reset_confirm.html'
  success_url = reverse_lazy('auth:password_reset_complete')

  def form_valid(self, form):
    messages.success(self.request, "Tu contraseña ha sido actualizada correctamente.")
    return super().form_valid(form)

  def form_invalid(self, form):
    return self.render_to_response(self.get_context_data(form=form))
