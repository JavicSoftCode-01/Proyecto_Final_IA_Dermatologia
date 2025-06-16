"""
Template tags para manejar imágenes de S3
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def s3_url(image_field):
    """
    Retorna la URL de S3 para un campo de imagen.
    """
    if image_field and hasattr(image_field, 'url'):
        try:
            return image_field.url
        except:
            return None
    return None

@register.filter
def has_profile_picture(user):
    """
    Verifica si el usuario tiene una imagen de perfil.
    """
    return user.profile_picture and bool(user.profile_picture.name)

@register.simple_tag
def default_profile_image():
    """
    Retorna la URL de la imagen de perfil por defecto.
    """
    return "/static/img/default-profile.png"
