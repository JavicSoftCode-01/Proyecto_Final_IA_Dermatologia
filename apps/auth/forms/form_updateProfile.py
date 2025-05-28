# apps/auth/forms/form_updateProfile.py
"""
Formulario para actualizar el perfil del usuario.
"""

from django.contrib.auth import get_user_model

from apps.auth.forms.form_auth import BaseUserForm

User = get_user_model()


class ProfileUpdateForm(BaseUserForm):
  """
  Formulario para actualizar la información del perfil del usuario.
  Hereda del formulario base y pre-llena los campos con la información actual.
  """

  class Meta(BaseUserForm.Meta):
    model = User
    fields = BaseUserForm.Meta.fields

  def __init__(self, *args, **kwargs):
    """
    Inicializa el formulario y pre-llena los campos con la información
    actual del usuario.
    """
    super().__init__(*args, **kwargs)
    self.fields['first_name'].initial = self.instance.first_name
    self.fields['last_name'].initial = self.instance.last_name
