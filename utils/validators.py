import re

from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils.translation import gettext_lazy as _


def validate_email(value):
  value = value.strip()  # Eliminar espacios en blanco

  if not value:
    raise ValidationError(
      _("El campo está vacío, por favor rellénelo.")
    )

  MaxLengthValidator(50, _("El correo electrónico no puede tener más de 50 caracteres."))(value)

  if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
    raise ValidationError(
      _("Ingrese un correo electrónico válido.")
    )


def validate_full_name(value):
  value = value.strip()  # Eliminar espacios en blanco

  if not value:
    raise ValidationError(
      _("El campo está vacío, por favor rellénelo.")
    )

  MinLengthValidator(3, _("El nombre o apellido debe tener al menos 3 caracteres."))(value)
  MaxLengthValidator(50, _("El nombre o apellido no puede tener más de 50 caracteres."))(value)

  if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
    raise ValidationError(
      _("Solo puede contener letras, incluyendo letras especiales como la Ñ o tilde.")
    )


def validate_dni(value):
  value = value.strip()  # Eliminar espacios en blanco

  MinLengthValidator(10, _('La cédula debe contener exactamente 10 dígitos.'))(value)
  MaxLengthValidator(10, _('La cédula debe contener exactamente 10 dígitos.'))(value)

  if not value.isdigit():
    raise ValidationError(_('La cédula debe contener solo números.'))

  coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
  total = 0
  for i in range(9):
    digito = int(value[i])
    coeficiente = coeficientes[i]
    producto = digito * coeficiente
    if producto > 9:
      producto -= 9
    total += producto

  digito_verificador = (total * 9) % 10
  if digito_verificador != int(value[9]):
    raise ValidationError(_('La cédula no es válida.'))


def validate_address_and_city(value):
  if value:
    value = value.strip()  # Eliminar espacios en blanco

    MaxLengthValidator(255, _("\"El campo no puede tener más de 255 caracteres.\""))(value)

    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ.\s]+$', value):
      raise ValidationError(
        _("\"El campo solo puede contener letras y espacios, incluyendo caracteres especiales como la Ñ, letras con tilde o Puntuación ( . ).\"")
      )


def validate_phone(value):
  if value:
    value = value.strip()  # Eliminar espacios en blanco

    MaxLengthValidator(16, _("\"El campo no puede tener más de 16 caracteres.\""))(value)

    if not re.match(r'^(\+593\s\d{2}\s\d{3}\s\d{4}|0\d{9})$', value):
      raise ValidationError(
        _("\"El teléfono debe estar en un formato válido, como 0995336523 o +593 99 533 6523. Solo digitos y el unico caracter ( + )\"")
      )


def validate_profile_picture(value):
  if value:
    valid_extensions = ['png', 'jpg', 'jpeg']
    if not value.name.split('.')[-1].lower() in valid_extensions:
      raise ValidationError(
        _("\"Solo se permiten imágenes en formato PNG, JPG o JPEG.\"")
      )
