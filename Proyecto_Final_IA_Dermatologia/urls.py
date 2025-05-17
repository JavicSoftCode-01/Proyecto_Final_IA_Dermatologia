from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
                path('admin/', admin.site.urls),
                path('dermatology/', include('core.Dermatologia_IA.urls')),  # Ruta para funciones IA
                path('', include('core.urls')),  # Ruta raíz va al HomeView
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
