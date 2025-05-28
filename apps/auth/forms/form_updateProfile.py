from django.contrib.auth import get_user_model

from apps.auth.forms.form_auth import ManagerFormsUser

User = get_user_model()


class ProfileUpdateForm(ManagerFormsUser):
  """
  Formulario para actualizar la información del perfil del usuario.
  """

  class Meta(ManagerFormsUser.Meta):
    model = User
    fields = ManagerFormsUser.Meta.fields

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['first_name'].initial = self.instance.first_name
    self.fields['last_name'].initial = self.instance.last_name
