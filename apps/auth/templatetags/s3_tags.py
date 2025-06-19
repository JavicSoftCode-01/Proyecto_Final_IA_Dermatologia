from django import template

register = template.Library()


@register.filter
def s3_url(image_field):
  if image_field and hasattr(image_field, 'url'):
    try:
      return image_field.url
    except Exception:
      return None
  return None


@register.filter
def has_profile_picture(user):
  if hasattr(user, 'profile_picture'):
    name = getattr(user.profile_picture, 'name', '')
    return bool(name)
  return False
