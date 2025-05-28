# core/Dermatologia_IA/views/generateReport_and_sendReportEmail.py

from django.contrib import messages
from django.shortcuts import redirect
from django.views import View

from apps.Dermatologia_IA.utils.generateReport import generate_report
from apps.Dermatologia_IA.utils.sendReportEmail import send_report_email
from apps.auth.views.view_auth import CustomLoginRequiredMixin


class GenerateReportView(CustomLoginRequiredMixin, View):
  """
   generar y descargar el reporte PDF.
  """

  def get(self, request, image_id):
    try:
      pdf_response = generate_report(image_id)
      if pdf_response:
        return pdf_response
      else:
        messages.error(request, "Error al generar el reporte PDF.")
        return redirect('dermatology:process_image', image_id=image_id)
    except Exception as e:
      print(f"Error crítico al generar el reporte PDF para imagen ID {image_id}: {e}")
      messages.error(request, "Ocurrió un error al generar el reporte. Por favor, contacte soporte.")
      return redirect('dermatology:process_image', image_id=image_id)


class SendReportEmailView(CustomLoginRequiredMixin, View):
  """
  enviar el reporte por email.
  """

  def post(self, request, image_id):
    email_address = request.POST.get('email')
    if email_address:
      try:
        success = send_report_email(image_id, email_address)
        if success:
          messages.success(request, f"Reporte enviado a {email_address} con éxito.")
        else:
          messages.error(request, "Error al enviar el email. Por favor, inténtelo de nuevo o contacte soporte.")
      except Exception as e:
        print(f"Error crítico al enviar el email para reporte ID {image_id}: {e}")
        messages.error(request, "Ocurrió un error al enviar el email. Por favor, contacte soporte.")
    else:
      messages.error(request, "Por favor, proporcione una dirección de email válida.")
    return redirect('dermatology:process_image', image_id=image_id)
