# apps/Dermatologia_IA/views/generateReport_and_sendReportEmail.py

"""
Módulo de vistas para la generación y envío de reportes dermatológicos.
"""

import logging

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, get_object_or_404
from django.views import View

from apps.Dermatologia_IA.models import SkinImage
from apps.Dermatologia_IA.utils.generateReport import generate_report
from apps.Dermatologia_IA.utils.sendReportEmail import EmailReportSender
from apps.auth.views.view_auth import CustomLoginRequiredMixin

logger = logging.getLogger(__name__)


class ReportActionMixin:
  """Mixin con funcionalidad común para las vistas de reportes"""

  def handle_error(
    self, request, error_msg, image_id, redirect_view="dermatology:process_image"
  ):
    """Maneja errores de forma consistente en las vistas de reportes"""
    logger.error(f"Error en reporte {image_id}: {error_msg}")
    messages.error(request, error_msg)
    return redirect(redirect_view, image_id=image_id)

  def validate_skin_image(self, image_id):
    """Valida que la imagen exista y esté procesada"""
    return get_object_or_404(SkinImage, id=image_id, processed=True)


class GenerateReportView(CustomLoginRequiredMixin, ReportActionMixin, View):
  """
  Vista para generar y descargar el reporte PDF de un análisis dermatológico.

  Genera un reporte detallado en PDF con los resultados del análisis
  y permite su descarga inmediata.
  """

  def get(self, request, image_id):
    try:
      # Validar que la imagen existe y está procesada
      self.validate_skin_image(image_id)

      # Generar el PDF
      pdf_response = generate_report(image_id)
      if not pdf_response:
        return self.handle_error(
          request,
          "No se pudo generar el reporte PDF. Por favor, inténtelo de nuevo.",
          image_id,
        )

      return pdf_response

    except Exception as e:
      return self.handle_error(
        request,
        "Ocurrió un error al generar el reporte. Por favor, contacte soporte.",
        image_id,
      )


class SendReportEmailView(CustomLoginRequiredMixin, ReportActionMixin, View):
  def post(self, request, image_id):
    try:
      self.validate_skin_image(image_id)
      email_address = request.POST.get("email")

      if not email_address:
        return self.handle_error(
          request,
          "Por favor, proporcione una dirección de email válida.",
          image_id,
          "dermatology:report_detail",
        )

      success = EmailReportSender.send_report(image_id, email_address)

      if success:
        messages.success(request, f"Reporte enviado exitosamente al Gmail {email_address}")
        logger.debug(f"Email sent successfully to {email_address}")
      else:
        return self.handle_error(
          request,
          "No se pudo enviar el email. Por favor, inténtelo de nuevo.",
          image_id,
          "dermatology:process_image",
        )

    except ValidationError as e:
      return self.handle_error(request, str(e), image_id, "dermatology:process_image")
    except Exception as e:
      return self.handle_error(
        request,
        "Ocurrió un error al enviar el email. Por favor, contacte soporte.",
        image_id,
        "dermatology:process_image",
      )

    return redirect('dermatology:process_image', image_id=image_id)
