# core/Dermatologia_IA/utils/sendReportEmail.py

from django.conf import settings
from django.core.mail import EmailMessage

from .generateReport import generate_report


def send_report_email(image_id, email_address):
  """
  Envía un reporte PDF por email al usuario.
  Args:
      image_id (int): ID de la imagen en la base de datos.
      email_address (str): Dirección de email del destinatario.
  Returns:
      bool: True si el email se envió correctamente, False en caso contrario.
  """
  try:
    # Generar el PDF
    pdf_response = generate_report(image_id)
    if pdf_response is None:
      print(f"Fallo en la generación del PDF para enviar por email (ID: {image_id}).")
      return False

    # Obtener el contenido binario del PDF
    pdf_content = pdf_response.content
    # Obtener el nombre de archivo del PDF
    content_disposition = pdf_response.get('Content-Disposition')
    pdf_filename = "reporte.pdf"
    if content_disposition and 'filename=' in content_disposition:
      parts = content_disposition.split('filename=')
      if len(parts) > 1:
        pdf_filename = parts[1].strip('"').strip("'")

    # Configurar el email
    email_subject = f'Reporte de Análisis Dermatológico Preliminar - ID {image_id}'
    email_body = f"""Estimado/a paciente,
        Adjunto encontrará el reporte preliminar de su análisis dermatológico basado en IA (ID: {image_id}).
        Incluye metadatos proporcionados como edad, sexo y localización.
        **Importante:** Este análisis es una herramienta de apoyo y no reemplaza la evaluación por un médico especialista. Le recomendamos encarecidamente que consulte a un dermatólogo para discutir estos resultados, obtener un diagnóstico definitivo y un plan de tratamiento adecuado.
        Saludos cordiales,
        [Nombre de tu Clínica/Servicio si aplica]
        """
    email_from = settings.DEFAULT_FROM_EMAIL
    email_to = [email_address]

    # Crear el objeto EmailMessage
    email_msg = EmailMessage(
      subject=email_subject,
      body=email_body,
      from_email=email_from,
      to=email_to
    )
    # Adjuntar el PDF
    email_msg.attach(pdf_filename, pdf_content, 'application/pdf')
    # Enviar el email
    email_msg.send()
    print(f"Email enviado a {email_address} para reporte ID {image_id}")
    return True

  except Exception as e:
    print(f"Error al enviar el email para reporte ID {image_id}: {e}")
    import traceback
    traceback.print_exc()
    return False
