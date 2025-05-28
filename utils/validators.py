import re

from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils.translation import gettext_lazy as _

# Constantes para validación
LONGITUD_MAXIMA_EMAIL = 50
LONGITUD_MINIMA_NOMBRE = 3
LONGITUD_MAXIMA_NOMBRE = 50
LONGITUD_CEDULA = 10
LONGITUD_MAXIMA_DIRECCION = 255
LONGITUD_MAXIMA_TELEFONO = 16
EXTENSIONES_IMAGEN_VALIDAS = ['png', 'jpg', 'jpeg']

def validar_campo_no_vacio(valor: str) -> str:
    """
    Valida que un campo no esté vacío y elimina espacios en blanco
    
    Args:
        valor: Texto a validar
        
    Returns:
        str: Texto sin espacios en blanco
        
    Raises:
        ValidationError: Si el campo está vacío
    """
    valor_limpio = valor.strip()
    if not valor_limpio:
        raise ValidationError(_("El campo está vacío, por favor rellénelo."))
    return valor_limpio

def validate_email(value: str) -> None:
    """
    Valida el formato de un correo electrónico.
    - Elimina espacios en blanco
    - Verifica longitud máxima
    - Valida formato usando expresión regular
    """
    valor_limpio = validar_campo_no_vacio(value)
    
    MaxLengthValidator(
        LONGITUD_MAXIMA_EMAIL, 
        _("El correo electrónico no puede tener más de 50 caracteres.")
    )(valor_limpio)

    patron_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(patron_email, valor_limpio):
        raise ValidationError(_("Ingrese un correo electrónico válido."))

def validate_full_name(value: str) -> None:
    """
    Valida un nombre completo.
    - Elimina espacios en blanco
    - Verifica longitud mínima y máxima
    - Valida que solo contenga letras y caracteres especiales permitidos
    """
    valor_limpio = validar_campo_no_vacio(value)

    MinLengthValidator(
        LONGITUD_MINIMA_NOMBRE, 
        _("El nombre o apellido debe tener al menos 3 caracteres.")
    )(valor_limpio)
    
    MaxLengthValidator(
        LONGITUD_MAXIMA_NOMBRE, 
        _("El nombre o apellido no puede tener más de 50 caracteres.")
    )(valor_limpio)

    patron_nombre = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$'
    if not re.match(patron_nombre, valor_limpio):
        raise ValidationError(
            _("Solo puede contener letras, incluyendo letras especiales como la Ñ o tilde.")
        )

def validate_dni(value: str) -> None:
    """
    Valida una cédula ecuatoriana usando el algoritmo de verificación oficial.
    
    El algoritmo aplica coeficientes específicos a cada dígito y verifica
    el último dígito (verificador) según la normativa ecuatoriana.
    """
    valor_limpio = validar_campo_no_vacio(value)

    # Validar longitud exacta de 10 dígitos
    MinLengthValidator(LONGITUD_CEDULA, _('La cédula debe contener exactamente 10 dígitos.'))(valor_limpio)
    MaxLengthValidator(LONGITUD_CEDULA, _('La cédula debe contener exactamente 10 dígitos.'))(valor_limpio)

    if not valor_limpio.isdigit():
        raise ValidationError(_('La cédula debe contener solo números.'))

    # Algoritmo de validación de cédula ecuatoriana
    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    total = sum(
        (digito * coef - 9 if digito * coef > 9 else digito * coef)
        for digito, coef in zip([int(d) for d in valor_limpio[:9]], coeficientes)
    )
    
    digito_verificador = (total * 9) % 10
    if digito_verificador != int(valor_limpio[9]):
        raise ValidationError(_('La cédula no es válida.'))

def validate_address_and_city(value: str) -> None:
    """
    Valida una dirección o ciudad si está presente.
    - Verifica longitud máxima
    - Valida caracteres permitidos (letras, espacios y puntos)
    """
    if value:
        valor_limpio = value.strip()
        MaxLengthValidator(
            LONGITUD_MAXIMA_DIRECCION, 
            _("El campo no puede tener más de 255 caracteres.")
        )(valor_limpio)

        patron_direccion = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ.\s]+$'
        if not re.match(patron_direccion, valor_limpio):
            raise ValidationError(
                _("El campo solo puede contener letras y espacios, incluyendo caracteres especiales como la Ñ, letras con tilde o Puntuación ( . ).")
            )

def validate_phone(value: str) -> None:
    """
    Valida un número telefónico ecuatoriano si está presente.
    Formatos válidos:
    - 0995336523 (10 dígitos)
    - +593 99 533 6523 (formato internacional)
    """
    if value:
        valor_limpio = value.strip()
        MaxLengthValidator(
            LONGITUD_MAXIMA_TELEFONO, 
            _("El campo no puede tener más de 16 caracteres.")
        )(valor_limpio)

        patron_telefono = r'^(\+593\s\d{2}\s\d{3}\s\d{4}|0\d{9})$'
        if not re.match(patron_telefono, valor_limpio):
            raise ValidationError(
                _("El teléfono debe estar en un formato válido, como 0995336523 o +593 99 533 6523. Solo digitos y el unico caracter ( + )")
            )

def validate_profile_picture(value) -> None:
    """
    Valida que una imagen de perfil tenga una extensión permitida.
    Extensiones válidas: PNG, JPG, JPEG
    """
    if value:
        extension = value.name.split('.')[-1].lower()
        if extension not in EXTENSIONES_IMAGEN_VALIDAS:
            raise ValidationError(
                _("Solo se permiten imágenes en formato PNG, JPG o JPEG.")
            )
