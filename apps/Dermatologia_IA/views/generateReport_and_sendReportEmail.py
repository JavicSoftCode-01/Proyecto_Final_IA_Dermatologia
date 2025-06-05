# # apps/Dermatologia_IA/views/generateReport_and_sendReportEmail.py
#
# import logging
#
# from django.contrib import messages
# from django.core.exceptions import ValidationError
# from django.shortcuts import redirect, get_object_or_404
# from django.urls import reverse
# from django.views import View
#
# from apps.Dermatologia_IA.models import SkinImage
# from apps.Dermatologia_IA.utils.generateReport import generate_report
# from apps.Dermatologia_IA.utils.sendReportEmail import EmailReportSender
# from apps.auth.views.view_auth import CustomLoginRequiredMixin
#
# logger = logging.getLogger(__name__)
#
#
# class ReportActionMixin:
#   """Mixin con funcionalidad común para las vistas de reportes"""
#
#   def handle_report_error(self, request, error_msg, image_id, redirect_view_name="dermatology:report_detail",
#                           redirect_show_actions=True):
#     """Maneja errores de forma consistente en las vistas de reportes, controlando si se muestran acciones en la redirección."""
#     logger.error(f"Error relacionado con SkinImage ID {image_id}: {error_msg}")
#     messages.error(request, error_msg)
#
#     # Construir la URL base para la redirección
#     redirect_url_base = reverse(redirect_view_name, kwargs={'image_id': image_id})
#
#     param_separator = "&" if "?" in redirect_url_base else "?"
#     redirect_url_final = f"{redirect_url_base}{param_separator}show_actions={'true' if redirect_show_actions else 'false'}"
#
#     return redirect(redirect_url_final)
#
#   def validate_skin_image(self, image_id):
#     """Valida que la imagen exista y esté procesada"""
#     return get_object_or_404(SkinImage, id=image_id, processed=True)
#
#
# class GenerateReportView(CustomLoginRequiredMixin, ReportActionMixin, View):
#   """
#   Vista para generar y descargar el reporte PDF de un análisis dermatológico.
#   Genera un reporte detallado en PDF con los resultados del análisis
#   y permite su descarga inmediata.
#   Si falla, redirige a la vista de procesamiento de imagen mostrando un error.
#   """
#
#   def get(self, request, image_id):
#     try:
#       self.validate_skin_image(image_id)
#       pdf_response = generate_report(image_id)
#       if not pdf_response:
#         # Si generate_report devuelve None o False (indicando fallo)
#         return self.handle_report_error(
#           request,
#           "No se pudo generar el reporte PDF. Por favor, inténtelo de nuevo.",
#           image_id,
#           redirect_view_name="dermatology:report_detail",  # O report_detail si es más apropiado
#           redirect_show_actions=True  # Mostrar acciones para reintentar
#         )
#
#       # Mensaje de éxito (opcional, ya que la acción principal es la descarga)
#       # messages.success(request, "El reporte PDF se ha generado y la descarga debería comenzar.")
#       return pdf_response
#
#     except SkinImage.DoesNotExist:
#       return self.handle_report_error(
#         request,
#         "El análisis de imagen especificado no existe o no ha sido procesado.",
#         image_id,
#         redirect_view_name="dermatology:report_list",  # Redirigir a la lista si la imagen no es válida
#         redirect_show_actions=True
#       )
#     except Exception as e:
#       # Error genérico durante la generación del PDF
#       return self.handle_report_error(
#         request,
#         f"Ocurrió un error inesperado al generar el reporte: {str(e)}. Por favor, contacte soporte.",
#         image_id,
#         redirect_view_name="dermatology:report_detail",  # O report_detail
#         redirect_show_actions=True  # Mostrar acciones
#       )
#
#
# class SendReportEmailView(CustomLoginRequiredMixin, ReportActionMixin, View):
#   """
#   Vista para enviar el reporte por email.
#   Redirige a la vista de detalle del reporte (results.html) después del intento,
#   controlando la visibilidad de los botones de acción.
#   """
#   results_view_name = 'dermatology:report_detail'
#
#   def post(self, request, image_id):
#     try:
#       skin_image = self.validate_skin_image(image_id)  # skin_image ahora está disponible
#       email_address = request.POST.get("email")
#
#       if not email_address:  # Validación básica del email
#         messages.error(request, "Por favor, proporcione una dirección de email válida.")
#         # Redirigir de vuelta a la página de detalle/resultados, mostrando acciones
#         redirect_url = reverse(self.results_view_name, kwargs={'image_id': image_id}) + "?show_actions=true"
#         return redirect(redirect_url)
#
#       success = EmailReportSender.send_report(skin_image.id, email_address)  # Usar skin_image.id
#
#       if success:
#         messages.success(request, f"Reporte enviado exitosamente a {email_address}")
#         logger.info(f"Reporte para SkinImage ID {skin_image.id} enviado a {email_address}")
#         # Redirigir a la vista de resultados SIN mostrar acciones
#         redirect_url = reverse(self.results_view_name, kwargs={'image_id': skin_image.id}) + "?show_actions=false"
#         return redirect(redirect_url)
#       else:
#         # EmailReportSender.send_report devolvió False
#         return self.handle_report_error(
#           request,
#           "No se pudo enviar el email. El servicio de correo pudo haber fallado. Por favor, inténtelo de nuevo.",
#           skin_image.id,
#           redirect_view_name=self.results_view_name,
#           redirect_show_actions=True  # Mostrar acciones para reintentar
#         )
#
#     except SkinImage.DoesNotExist:
#       return self.handle_report_error(
#         request,
#         "El análisis de imagen especificado no existe o no ha sido procesado.",
#         image_id,  # image_id original ya que skin_image no se encontró
#         redirect_view_name="dermatology:report_list",
#         redirect_show_actions=True
#       )
#     except ValidationError as e:  # Capturar ValidationError específicamente
#       # Esto podría venir de una validación de email más robusta si EmailReportSender la hiciera
#       error_message = ", ".join(e.messages) if hasattr(e, 'messages') else str(e)
#       return self.handle_report_error(
#         request,
#         f"Error de validación al intentar enviar el email: {error_message}",
#         image_id,  # image_id original
#         redirect_view_name=self.results_view_name,
#         redirect_show_actions=True
#       )
#     except Exception as e:
#       # Error genérico
#       return self.handle_report_error(
#         request,
#         f"Ocurrió un error inesperado al enviar el email: {str(e)}. Por favor, contacte soporte.",
#         image_id,  # image_id original
#         redirect_view_name=self.results_view_name,
#         redirect_show_actions=True  # Mostrar acciones
#       )
# apps/Dermatologia_IA/views/generateReport_and_sendReportEmail.py

import logging

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views import View

from apps.Dermatologia_IA.models import SkinImage
from apps.Dermatologia_IA.utils.generateReport import generate_report
from apps.Dermatologia_IA.utils.sendReportEmail import EmailReportSender
from apps.auth.views.view_auth import CustomLoginRequiredMixin

logger = logging.getLogger(__name__)


class ReportActionMixin:
  """Mixin con funcionalidad común para las vistas de reportes"""

  def handle_report_error(self, request, error_msg, image_id, redirect_view_name="dermatology:report_detail",
                          redirect_show_actions=True):
    """Maneja errores de forma consistente en las vistas de reportes, controlando si se muestran acciones en la redirección."""
    logger.error(f"Error relacionado con SkinImage ID {image_id}: {error_msg}")
    messages.error(request, error_msg)

    # Construir la URL base para la redirección
    redirect_url_base = reverse(redirect_view_name, kwargs={'image_id': image_id})

    param_separator = "&" if "?" in redirect_url_base else "?"
    redirect_url_final = f"{redirect_url_base}{param_separator}show_actions={'true' if redirect_show_actions else 'false'}"

    return redirect(redirect_url_final)

  def validate_skin_image(self, image_id):
    """Valida que la imagen exista y esté procesada"""
    return get_object_or_404(SkinImage, id=image_id, processed=True)


# class GenerateReportView(CustomLoginRequiredMixin, ReportActionMixin, View):
#   """
#   Vista para generar y descargar el reporte PDF de un análisis dermatológico.
#   Genera un reporte detallado en PDF con los resultados del análisis,
#   permite su descarga inmediata y luego redirige automáticamente a report_detail sin botones.
#   Si falla, redirige a la vista de procesamiento de imagen mostrando un error.
#   """
#
#   def get(self, request, image_id):
#     try:
#       skin_image = self.validate_skin_image(image_id)
#       pdf_response = generate_report(image_id)
#
#       if not pdf_response:
#         # Si generate_report devuelve None o False (indicando fallo)
#         return self.handle_report_error(
#           request,
#           "No se pudo generar el reporte PDF. Por favor, inténtelo de nuevo.",
#           image_id,
#           redirect_view_name="dermatology:report_detail",
#           redirect_show_actions=True  # Mostrar acciones para reintentar
#         )
#
#       # Si el PDF se generó exitosamente, agregamos JavaScript para redireccionar después de la descarga
#       if isinstance(pdf_response, HttpResponse):
#         # Agregar JavaScript para redireccionar después de la descarga
#         redirect_url = reverse("dermatology:report_detail", kwargs={'image_id': image_id}) + "?show_actions=false"
#
#         # Crear el script de redirección
#         redirect_script = f"""
#         <script>
#           // Esperar un momento para que la descarga inicie y luego redireccionar
#           setTimeout(function() {{
#             window.location.href = '{redirect_url}';
#           }}, 1000);
#         </script>
#         """
#
#         # Si la respuesta es HTML, agregar el script
#         if pdf_response.get('Content-Type', '').startswith('text/html'):
#           # Si es HTML, agregar el script al contenido
#           content = pdf_response.content.decode('utf-8')
#           content = content.replace('</body>', f'{redirect_script}</body>')
#           pdf_response.content = content.encode('utf-8')
#         else:
#           # Si es PDF, agregar headers para forzar descarga y redirección con meta refresh
#           pdf_response['Content-Disposition'] = f'attachment; filename="reporte_dermatologico_{image_id}.pdf"'
#
#           # Crear una respuesta HTML que descargue el PDF y redirija
#           html_response = HttpResponse(f"""
#           <!DOCTYPE html>
#           <html>
#           <head>
#               <meta charset="utf-8">
#               <title>Descargando reporte...</title>
#               <meta http-equiv="refresh" content="2;url={redirect_url}">
#           </head>
#           <body>
#               <div style="text-align: center; margin-top: 50px; font-family: Arial, sans-serif;">
#                   <h3>Generando reporte PDF...</h3>
#                   <p>La descarga debería comenzar automáticamente.</p>
#                   <p>Serás redirigido en unos segundos.</p>
#                   <script>
#                       // Crear enlace temporal para descarga
#                       const link = document.createElement('a');
#                       link.href = '{request.build_absolute_uri()}';
#                       link.download = 'reporte_dermatologico_{image_id}.pdf';
#                       document.body.appendChild(link);
#                       link.click();
#                       document.body.removeChild(link);
#
#                       // Redireccionar después de 2 segundos
#                       setTimeout(function() {{
#                           window.location.href = '{redirect_url}';
#                       }}, 2000);
#                   </script>
#               </div>
#           </body>
#           </html>
#           """, content_type='text/html')
#
#           return html_response
#
#         return pdf_response
#       else:
#         # Si pdf_response no es una HttpResponse válida, retornarlo (descarga directa)
#         return pdf_response
#
#     except SkinImage.DoesNotExist:
#       return self.handle_report_error(
#         request,
#         "El análisis de imagen especificado no existe o no ha sido procesado.",
#         image_id,
#         redirect_view_name="dermatology:report_list",  # Redirigir a la lista si la imagen no es válida
#         redirect_show_actions=True
#       )
#     except Exception as e:
#       # Error genérico durante la generación del PDF
#       return self.handle_report_error(
#         request,
#         f"Ocurrió un error inesperado al generar el reporte: {str(e)}. Por favor, contacte soporte.",
#         image_id,
#         redirect_view_name="dermatology:report_detail",
#         redirect_show_actions=True  # Mostrar acciones
#       )

class GenerateReportView(CustomLoginRequiredMixin, ReportActionMixin, View):
  """
  Vista para generar y descargar el reporte PDF de un análisis dermatológico.
  Genera un reporte detallado en PDF con los resultados del análisis,
  permite su descarga inmediata y luego redirige automáticamente a report_detail sin botones.
  Si falla, redirige a la vista de procesamiento de imagen mostrando un error.
  """

  def get(self, request, image_id):
    try:
      skin_image = self.validate_skin_image(image_id)
      pdf_response = generate_report(image_id)

      if not pdf_response:
        # Si generate_report devuelve None o False (indicando fallo)
        return self.handle_report_error(
          request,
          "No se pudo generar el reporte PDF. Por favor, inténtelo de nuevo.",
          image_id,
          redirect_view_name="dermatology:report_detail",
          redirect_show_actions=True  # Mostrar acciones para reintentar
        )

      # Si el PDF se generó exitosamente, agregamos JavaScript para redireccionar después de la descarga
      if isinstance(pdf_response, HttpResponse):
        redirect_url = reverse("dermatology:report_detail", kwargs={'image_id': image_id}) + "?show_actions=false"

        # Si la respuesta es HTML, agregamos el script al contenido (opcional)
        if pdf_response.get('Content-Type', '').startswith('text/html'):
          content = pdf_response.content.decode('utf-8')
          # Si ya tienes una página HTML normal, aquí podrías insertar solo el <script> si quieres.
          content = content.replace(
            '</body>',
            f'<script>setTimeout(function() {{ window.location.href = "{redirect_url}"; }}, 1000);</script></body>'
          )
          pdf_response.content = content.encode('utf-8')
          return pdf_response
        else:
          # Si es PDF, forzamos descarga y devolvemos solo el fragmento del modal
          pdf_response['Content-Disposition'] = f'attachment; filename="reporte_dermatologico_{image_id}.pdf"'

          # --------------------------------------------------------------------------------
          # Fragmento HTML MÍNIMO: solo modal
          # --------------------------------------------------------------------------------
          fragment = f"""
<!-- Estilos inline para el modal y backdrop -->
<style>
  /* Fondo semitransparente que ocupa toda la ventana */
  .modal-backdrop {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
background-color: rgba(0, 0, 0, 0);
    z-index: 1000;
  }}

  /* Contenedor central pequeño */
  .modal-container {{
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 400px;          /* Puedes cambiar este ancho */
    max-width: 90%;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    z-index: 1001;
    font-family: Arial, sans-serif;
    padding: 20px;
    text-align: center;
  }}

  .modal-container h3 {{
    margin-top: 0;
    font-size: 1.25rem;
  }}

  .modal-container p {{
    margin: 10px 0;
    font-size: 1rem;
  }}
</style>

<!-- Fondo oscurecido -->
<div class="modal-backdrop"></div>

<!-- Cuerpo del modal -->
<div class="modal-container">
  <h3>Generando reporte PDF...</h3>
  <p>La descarga debería comenzar automáticamente.</p>
  <p>Serás redirigido en unos segundos.</p>
</div>

<!-- Script que dispara la descarga y hace la redirección -->
<script>
  // Crear un enlace invisible para forzar la descarga del PDF
  const link = document.createElement('a');
  link.href = '{request.build_absolute_uri()}';
  link.download = 'reporte_dermatologico_{image_id}.pdf';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // Redireccionar después de 2 segundos
  setTimeout(function() {{
    window.location.href = '{redirect_url}';
  }}, 2000);
</script>
                    """

          return HttpResponse(fragment, content_type='text/html')

      else:
        # Si pdf_response no es una HttpResponse válida, retornarlo (descarga directa)
        return pdf_response

    except SkinImage.DoesNotExist:
      return self.handle_report_error(
        request,
        "El análisis de imagen especificado no existe o no ha sido procesado.",
        image_id,
        redirect_view_name="dermatology:report_list",
        redirect_show_actions=True
      )
    except Exception as e:
      return self.handle_report_error(
        request,
        f"Ocurrió un error inesperado al generar el reporte: {str(e)}. Por favor, contacte soporte.",
        image_id,
        redirect_view_name="dermatology:report_detail",
        redirect_show_actions=True
      )


class SendReportEmailView(CustomLoginRequiredMixin, ReportActionMixin, View):
  """
  Vista para enviar el reporte por email.
  Redirige a la vista de detalle del reporte (results.html) después del intento,
  controlando la visibilidad de los botones de acción.
  """
  results_view_name = 'dermatology:report_detail'

  def post(self, request, image_id):
    try:
      skin_image = self.validate_skin_image(image_id)  # skin_image ahora está disponible
      email_address = request.POST.get("email")

      if not email_address:  # Validación básica del email
        messages.error(request, "Por favor, proporcione una dirección de email válida.")
        # Redirigir de vuelta a la página de detalle/resultados, mostrando acciones
        redirect_url = reverse(self.results_view_name, kwargs={'image_id': image_id}) + "?show_actions=true"
        return redirect(redirect_url)

      success = EmailReportSender.send_report(skin_image.id, email_address)  # Usar skin_image.id

      if success:
        messages.success(request, f"Reporte enviado exitosamente a {email_address}")
        logger.info(f"Reporte para SkinImage ID {skin_image.id} enviado a {email_address}")
        # Redirigir a la vista de resultados SIN mostrar acciones
        redirect_url = reverse(self.results_view_name, kwargs={'image_id': skin_image.id}) + "?show_actions=false"
        return redirect(redirect_url)
      else:
        # EmailReportSender.send_report devolvió False
        return self.handle_report_error(
          request,
          "No se pudo enviar el email. El servicio de correo pudo haber fallado. Por favor, inténtelo de nuevo.",
          skin_image.id,
          redirect_view_name=self.results_view_name,
          redirect_show_actions=True  # Mostrar acciones para reintentar
        )

    except SkinImage.DoesNotExist:
      return self.handle_report_error(
        request,
        "El análisis de imagen especificado no existe o no ha sido procesado.",
        image_id,  # image_id original ya que skin_image no se encontró
        redirect_view_name="dermatology:report_list",
        redirect_show_actions=True
      )
    except ValidationError as e:  # Capturar ValidationError específicamente
      # Esto podría venir de una validación de email más robusta si EmailReportSender la hiciera
      error_message = ", ".join(e.messages) if hasattr(e, 'messages') else str(e)
      return self.handle_report_error(
        request,
        f"Error de validación al intentar enviar el email: {error_message}",
        image_id,  # image_id original
        redirect_view_name=self.results_view_name,
        redirect_show_actions=True
      )
    except Exception as e:
      # Error genérico
      return self.handle_report_error(
        request,
        f"Ocurrió un error inesperado al enviar el email: {str(e)}. Por favor, contacte soporte.",
        image_id,  # image_id original
        redirect_view_name=self.results_view_name,
        redirect_show_actions=True  # Mostrar acciones
      )
