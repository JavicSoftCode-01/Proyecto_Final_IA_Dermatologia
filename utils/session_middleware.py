"""
Middleware para manejar el tiempo de sesión de los usuarios en Django.
Este middleware verifica la actividad del usuario y cierra la sesión si ha estado inactivo por más tiempo del permitido.
    Uso:
    Añadir `SessionTimeoutMiddleware` a la lista de middlewares en `settings.py`:
MIDDLEWARE = [
    ...
    'utils.session_middleware.SessionTimeoutMiddleware',
    ...
"""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import logout
from django.utils import timezone


class SessionTimeoutMiddleware:
  """
  Middleware para manejar el tiempo de sesión de los usuarios.
  Este middleware verifica la actividad del usuario y cierra la sesión si ha estado inactivo por más tiempo del permitido.
  """

  def __init__(self, get_response):
    self.get_response = get_response

  def __call__(self, request):
    if request.user.is_authenticated:
      last_activity = request.session.get('last_activity')

      if last_activity:
        last_activity = timezone.datetime.fromisoformat(last_activity)

        if timezone.now() - last_activity > timedelta(seconds=settings.SESSION_COOKIE_AGE):
          logout(request)
      request.session['last_activity'] = timezone.now().isoformat()

    response = self.get_response(request)
    return response
