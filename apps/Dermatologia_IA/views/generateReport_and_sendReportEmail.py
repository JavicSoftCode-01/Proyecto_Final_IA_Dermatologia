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

  def handle_report_error(
    self,
    request,
    error_msg,
    image_id,
    redirect_view_name="dermatology:report_detail",
    redirect_show_actions=True
  ):
    """Maneja errores de forma consistente en las vistas de reportes, controlando si se muestran acciones en la redirección."""
    logger.error(f"Error relacionado con SkinImage ID {image_id}: {error_msg}")
    messages.error(request, error_msg)

    redirect_url_base = reverse(redirect_view_name, kwargs={"image_id": image_id})
    param_separator = "&" if "?" in redirect_url_base else "?"
    redirect_url_final = (
      f"{redirect_url_base}"
      f"{param_separator}"
      f"show_actions={'true' if redirect_show_actions else 'false'}"
    )
    return redirect(redirect_url_final)

  def validate_skin_image(self, image_id):
    """Valida que la imagen exista y esté procesada"""
    return get_object_or_404(SkinImage, id=image_id, processed=True)


class GenerateReportView(CustomLoginRequiredMixin, ReportActionMixin, View):
  """
  Vista para generar y descargar el reporte PDF de un análisis dermatológico.
  Genera un reporte detallado en PDF con los resultados del análisis,
  permite su descarga inmediata y luego redirige automáticamente a report_detail.
  """

  def get(self, request, image_id):
    try:
      skin_image = self.validate_skin_image(image_id)
      pdf_response = generate_report(image_id)

      if not pdf_response:
        return self.handle_report_error(
          request,
          "No se pudo generar el reporte PDF. Por favor, inténtelo de nuevo.",
          image_id,
          redirect_view_name="dermatology:report_detail",
          redirect_show_actions=True,
        )

      # Preparar datos de éxito
      patient_name = skin_image.patient.get_full_name()
      consultation_date = skin_image.created_at.strftime("%d/%m/%Y %H:%M")

      # URL de redirección con datos en query params
      redirect_url = reverse("dermatology:report_detail", kwargs={"image_id": image_id})
      redirect_url += f"?show_actions=false&patient_name={patient_name}&consultation_date={consultation_date}"

      # HTML que dispara la descarga y luego redirige
      html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Descargando Reporte</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: Arial, sans-serif;
            background-color: #f8f9fa;
        }}
        .modal-container {{
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 400px;
            width: 90%;
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
</head>
<body>
    <div class="modal-container">
        <h3>Generando reporte PDF...</h3>
        <p>La descarga debería comenzar automáticamente.</p>
        <p>Serás redirigido en unos segundos.</p>
    </div>
    <script>
        // Trigger the PDF download
        const link = document.createElement("a");
        link.href = "{request.build_absolute_uri()}?download=true";
        link.download = "reporte_dermatologico_{image_id}.pdf";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Redirect after 2 seconds
        setTimeout(function() {{
            window.location.href = "{redirect_url}";
        }}, 2000);
    </script>
</body>
</html>
            """

      # Si se solicita descarga directa, devolver la respuesta PDF
      if request.GET.get("download") == "true":
        return pdf_response

      return HttpResponse(html_content, content_type="text/html")

    except SkinImage.DoesNotExist:
      return self.handle_report_error(
        request,
        "El análisis de imagen especificado no existe o no ha sido procesado.",
        image_id,
        redirect_view_name="dermatology:report_list",
        redirect_show_actions=True,
      )
    except Exception as e:
      return self.handle_report_error(
        request,
        f"Ocurrió un error inesperado al generar el reporte: {str(e)}. Por favor, contacte soporte.",
        image_id,
        redirect_view_name="dermatology:report_detail",
        redirect_show_actions=True,
      )


class SendReportEmailView(CustomLoginRequiredMixin, ReportActionMixin, View):
  """
  Vista para enviar el reporte por email.
  Redirige a la vista de detalle del reporte (results.html) después del intento.
  """

  results_view_name = "dermatology:report_detail"

  def post(self, request, image_id):
    try:
      skin_image = self.validate_skin_image(image_id)
      email_address = request.POST.get("email")

      if not email_address:
        messages.error(request, "Por favor, proporcione una dirección de email válida.")
        redirect_url = (
          reverse(self.results_view_name, kwargs={"image_id": image_id})
          + "?show_actions=true"
        )
        return redirect(redirect_url)

      success = EmailReportSender.send_report(skin_image.id, email_address)

      if success:
        messages.success(request, f"Reporte enviado exitosamente a {email_address}")
        logger.info(f"Reporte para SkinImage ID {skin_image.id} enviado a {email_address}")
        redirect_url = (
          reverse(self.results_view_name, kwargs={"image_id": image_id})
          + "?show_actions=false"
        )
        return redirect(redirect_url)
      else:
        return self.handle_report_error(
          request,
          "No se pudo enviar el email. El servicio de correo pudo haber fallado. Por favor, inténtelo de nuevo.",
          image_id,
          redirect_view_name=self.results_view_name,
          redirect_show_actions=True,
        )

    except SkinImage.DoesNotExist:
      return self.handle_report_error(
        request,
        "El análisis de imagen especificado no existe o no ha sido procesado.",
        image_id,
        redirect_view_name="dermatology:report_list",
        redirect_show_actions=True,
      )
    except ValidationError as e:
      error_message = ", ".join(e.messages) if hasattr(e, "messages") else str(e)
      return self.handle_report_error(
        request,
        f"Error de validación al intentar enviar el email: {error_message}",
        image_id,
        redirect_view_name=self.results_view_name,
        redirect_show_actions=True,
      )
    except Exception as e:
      return self.handle_report_error(
        request,
        f"Ocurrió un error inesperado al enviar el email: {str(e)}. Por favor, contacte soporte.",
        image_id,
        redirect_view_name=self.results_view_name,
        redirect_show_actions=True,
      )
