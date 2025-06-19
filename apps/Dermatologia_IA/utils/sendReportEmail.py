"""
  Módulo para enviar reportes por email en la aplicación Dermatología IA.
  Este módulo contiene la función `send_report_email` que envía un reporte PDF
    de un análisis dermatológico a la dirección de email del paciente.
    Utiliza la función `generate_report` para generar el PDF y envía el email
    utilizando la clase `EmailMessage` de Django."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage

from apps.Dermatologia_IA.models import SkinImage
from .generateReport import generate_report
from utils.logger import logger


def send_report_email(image_id, email_address):
    """
    Envía un reporte PDF por email al usuario.

    Args:
        image_id (int): ID de la imagen en la base de datos
        email_address (str): Dirección de email del destinatario

    Returns:
        bool: True si el email se envió correctamente, False en caso contrario

    Raises:
        ValidationError: Si los datos proporcionados son inválidos
    """

    logger.info('send_report_email', f'Intentando enviar reporte ID {image_id} a {email_address}')
    try:
        skin_image = SkinImage.objects.get(id=image_id, processed=True)

        pdf_response = generate_report(image_id)
        if not pdf_response:
            logger.error('send_report_email', f'Fallo en la generación del PDF para email (ID: {image_id})')
            return False

        nombre = skin_image.patient.get_full_name() if hasattr(skin_image.patient, 'get_full_name') else ''
        dni = skin_image.patient.dni or ''
        subject = f'Reporte de Análisis Dermatológico Preliminar - ID {image_id}'
        body = (
            f"Estimado/a {nombre},\n"
            f"DNI: {dni}\n\n"
            f"Adjunto encontrará el reporte preliminar de su análisis "
            f"dermatológico basado en IA (ID: {image_id}).\n\n"
            "Este es un análisis preliminar generado por inteligencia "
            "artificial y debe ser validado por un profesional médico.\n\n"
            "Saludos cordiales,\n"
            "Derma IA"
        )

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email_address]
        )

        content_disposition = pdf_response.get('Content-Disposition')
        if not content_disposition or 'filename=' not in content_disposition:
            filename = "reporte_dermatologico.pdf"
        else:
            try:
                parts = content_disposition.split('filename=')
                filename = parts[1].strip('"').strip("'")
            except IndexError:
                filename = "reporte_dermatologico.pdf"
        email.attach(filename, pdf_response.content, 'application/pdf')

        email.send()
        logger.info('send_report_email', f'Email enviado exitosamente a {email_address} para reporte ID {image_id}')
        return True

    except SkinImage.DoesNotExist:
        logger.error('send_report_email', f'No se encontró la imagen con ID {image_id} o no está procesada')
        raise ValidationError("El reporte solicitado no existe o no está listo")

    except Exception as e:
        logger.error('send_report_email', f'Error al enviar email para reporte ID {image_id}: {str(e)}')
        return False
