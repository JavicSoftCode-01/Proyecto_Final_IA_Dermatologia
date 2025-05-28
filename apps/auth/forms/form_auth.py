# apps/auth/forms/form_auth.py
"""
Formulario de autenticación personalizado para la aplicación auth.
Incluye formularios para registro, inicio de sesión y cambio de contraseña.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm

User = get_user_model()


class BaseUserForm(forms.ModelForm):
  """
  Formulario base para la gestión de usuarios.
  Contiene todos los campos comunes y la configuración de widgets.
  """

  # Campos de identificación
  email = forms.EmailField(
    label='Correo electrónico',
    required=True,
    widget=forms.EmailInput(attrs={
      'class': 'form-control',
      'placeholder': 'Correo electrónico'
    })
  )

  # Información personal
  first_name = forms.CharField(
    label='Nombres',
    max_length=50,
    required=True,
    widget=forms.TextInput(attrs={
      'class': 'form-control',
      'placeholder': 'Nombres'
    })
  )

  last_name = forms.CharField(
    label='Apellidos',
    max_length=50,
    required=True,
    widget=forms.TextInput(attrs={
      'class': 'form-control',
      'placeholder': 'Apellidos'
    })
  )

  dni = forms.CharField(
    label='Cédula',
    max_length=10,
    required=False,
    widget=forms.TextInput(attrs={
      'class': 'form-control',
      'placeholder': 'Cédula'
    })
  )

  # Información de contacto
  address = forms.CharField(
    label='Dirección',
    max_length=255,
    required=False,
    widget=forms.TextInput(attrs={
      'class': 'form-control',
      'placeholder': 'Dirección'
    })
  )

  city = forms.CharField(
    label='Ciudad',
    max_length=255,
    required=False,
    widget=forms.TextInput(attrs={
      'class': 'form-control',
      'placeholder': 'Ciudad'
    })
  )

  phone = forms.CharField(
    label='Teléfono',
    max_length=20,
    required=False,
    widget=forms.TextInput(attrs={
      'class': 'form-control',
      'placeholder': 'Teléfono'
    })
  )

  # Imagen de perfil
  profile_picture = forms.ImageField(
    label='Foto de perfil',
    required=False,
    widget=forms.FileInput(attrs={
      'class': 'form-control',
      'placeholder': 'Foto de perfil'
    })
  )

  class Meta:
    model = User
    fields = [
      'email', 'first_name', 'last_name', 'dni',
      'address', 'city', 'phone', 'profile_picture'
    ]


class CustomUserCreationForm(BaseUserForm, UserCreationForm):
  """
  Formulario para la creación de nuevos usuarios.
  Extiende el formulario base y añade los campos de contraseña.
  """
  password1 = forms.CharField(
    label='Contraseña',
    widget=forms.PasswordInput(attrs={
      'class': 'form-control',
      'placeholder': 'Contraseña'
    })
  )

  password2 = forms.CharField(
    label='Confirmar contraseña',
    widget=forms.PasswordInput(attrs={
      'class': 'form-control',
      'placeholder': 'Confirmar contraseña'
    })
  )

  class Meta(BaseUserForm.Meta):
    fields = BaseUserForm.Meta.fields + ['password1', 'password2']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.error_messages['password_mismatch'] = 'Las contraseñas no coinciden.'


class CustomAuthenticationForm(AuthenticationForm):
  """
  Formulario para la autenticación de usuarios.
  Personaliza los campos de inicio de sesión.
  """
  username = forms.EmailField(
    label='Correo electrónico',
    widget=forms.EmailInput(attrs={
      'class': 'form-control',
      'placeholder': 'Correo electrónico'
    })
  )

  password = forms.CharField(
    label='Contraseña',
    widget=forms.PasswordInput(attrs={
      'class': 'form-control',
      'placeholder': 'Contraseña'
    })
  )


class CustomSetPasswordForm(SetPasswordForm):
  """
  Formulario para cambiar la contraseña del usuario.
  Personaliza los campos y mensajes de error.
  """

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._setup_fields()

  def _setup_fields(self):
    """Configura los atributos y etiquetas de los campos del formulario"""
    self.fields['new_password1'].widget = forms.PasswordInput(attrs={
      'class': 'form-control',
      'placeholder': 'Ingrese su nueva contraseña'
    })
    self.fields['new_password1'].label = 'Nueva contraseña'

    self.fields['new_password2'].widget = forms.PasswordInput(attrs={
      'class': 'form-control',
      'placeholder': 'Confirme su nueva contraseña'
    })
    self.fields['new_password2'].label = 'Confirmar nueva contraseña'

  def clean(self):
    """Valida que las contraseñas coincidan"""
    cleaned_data = super().clean()
    password1 = cleaned_data.get('new_password1')
    password2 = cleaned_data.get('new_password2')

    if password1 and password2 and password1 != password2:
      self.add_error('new_password2', 'Las contraseñas no coinciden.')

    return cleaned_data
