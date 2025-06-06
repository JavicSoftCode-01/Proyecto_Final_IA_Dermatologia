# utils\session_middleware.py

"""
    Middleware para manejar el tiempo de sesión de los usuarios.
    Este middleware verifica la actividad del usuario y cierra la sesión
        si ha estado inactivo por más tiempo del permitido.
        """

from django.contrib.auth import logout
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Obtener el tiempo de la última actividad
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                # Convertir el tiempo de la última actividad a objeto datetime
                last_activity = timezone.datetime.fromisoformat(last_activity)
                
                # Verificar si ha pasado el tiempo límite 
                if timezone.now() - last_activity > timedelta(seconds=settings.SESSION_COOKIE_AGE):
                    # Si pasó el tiempo límite, cerrar sesión
                    logout(request)
                    # La siguiente página que cargue redirigirá al login debido a @login_required
            
            # Actualizar el tiempo de última actividad
            request.session['last_activity'] = timezone.now().isoformat()

        response = self.get_response(request)
        return response
