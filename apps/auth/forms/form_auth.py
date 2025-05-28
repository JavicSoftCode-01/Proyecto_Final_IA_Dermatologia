# apps/auth/forms/form_auth.py

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm

User = get_user_model()


class ManagerFormsUser(forms.ModelForm):
  email = forms.EmailField(
    label='Correo electrónico',
    required=True,
    widget=forms.EmailInput(attrs={
      'class': 'form-control',
      'placeholder': 'Correo electrónico'
    })
  )
  first_name = forms.CharField(
    label='Nombres',
    max_length=50,
    required=True,
    widget=forms.TextInput(attrs={
      'class': 'form-control',
      'placeholder': 'Nombre'
    })
  )
  last_name = forms.CharField(
    label='Apellidos',
    max_length=50,
    required=True,
    widget=forms.TextInput(attrs={
      'class': 'form-control',
      'placeholder': 'Apellido'
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
    fields = ['email', 'first_name', 'last_name', 'dni', 'address', 'city', 'phone', 'profile_picture']


class CustomUserCreationForm(ManagerFormsUser, UserCreationForm):
  password1 = forms.CharField(
    widget=forms.PasswordInput(attrs={
      'class': 'form-control',
      'placeholder': 'Contraseña'
    })
  )
  password2 = forms.CharField(
    widget=forms.PasswordInput(attrs={
      'class': 'form-control',
      'placeholder': 'Confirmar contraseña'
    })
  )

  class Meta(ManagerFormsUser.Meta):
    fields = ManagerFormsUser.Meta.fields + ['password1', 'password2']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.error_messages['password_mismatch'] = 'Las contraseñas no coinciden.'


class CustomAuthenticationForm(AuthenticationForm):
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

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)


class CustomSetPasswordForm(SetPasswordForm):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['new_password1'].widget.attrs.update({
      'class': 'form-control',
      'placeholder': 'Ingrese su nueva contraseña'
    })
    self.fields['new_password2'].widget.attrs.update({
      'class': 'form-control',
      'placeholder': 'Confirme su nueva contraseña'
    })
    self.fields['new_password1'].label = 'Nueva contraseña'
    self.fields['new_password2'].label = 'Confirmar nueva contraseña'

  def clean(self):
    cleaned_data = super().clean()
    password1 = cleaned_data.get('new_password1')
    password2 = cleaned_data.get('new_password2')
    if password1 and password2 and password1 != password2:
      self.add_error('new_password2', 'Las contraseñas no coinciden.')
    return cleaned_data
