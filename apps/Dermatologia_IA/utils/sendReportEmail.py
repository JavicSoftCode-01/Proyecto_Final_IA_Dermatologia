"""
Módulo para el envío de reportes por correo electrónico.
Maneja la generación y envío de reportes PDF de análisis dermatológicos.
"""
import logging
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.exceptions import ValidationError

from apps.Dermatologia_IA.models import SkinImage
from .generateReport import generate_report

logger = logging.getLogger(__name__)

class EmailReportSender:
    """
    Clase encargada de preparar y enviar reportes por correo electrónico.
    Implementa la lógica de composición y envío de emails con reportes adjuntos.
    """

    @staticmethod
    def _get_pdf_filename(content_disposition):
        """Extrae el nombre del archivo PDF del Content-Disposition"""
        if not content_disposition or 'filename=' not in content_disposition:
            return "reporte_dermatologico.pdf"
        
        try:
            parts = content_disposition.split('filename=')
            return parts[1].strip('"').strip("'")
        except IndexError:
            return "reporte_dermatologico.pdf"

    @staticmethod
    def _prepare_email_content(patient, image_id):
        """Prepara el asunto y cuerpo del correo"""
        first_name = patient.first_name or ''
        last_name = patient.last_name or ''
        dni = patient.dni or ''

        subject = f'Reporte de Análisis Dermatológico Preliminar - ID {image_id}'
        body = (
            f"Estimado/a {first_name} {last_name},\n"
            f"DNI: {dni}\n\n"
            f"Adjunto encontrará el reporte preliminar de su análisis "
            f"dermatológico basado en IA (ID: {image_id}).\n\n"
            "Este es un análisis preliminar generado por inteligencia "
            "artificial y debe ser validado por un profesional médico.\n\n"
            "Saludos cordiales,\n"
            "Derma IA"
        )
        return subject, body

    @classmethod
    def send_report(cls, image_id, email_address):
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
        try:
            # Validar que la imagen existe y está procesada
            skin_image = SkinImage.objects.get(id=image_id, processed=True)
            
            # Generar el PDF
            pdf_response = generate_report(image_id)
            if not pdf_response:
                logger.error(f"Fallo en la generación del PDF para email (ID: {image_id})")
                return False

            # Preparar el contenido del email
            subject, body = cls._prepare_email_content(skin_image.patient, image_id)
            
            # Configurar y enviar el email
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_address]
            )

            # Adjuntar el PDF
            filename = cls._get_pdf_filename(pdf_response.get('Content-Disposition'))
            email.attach(filename, pdf_response.content, 'application/pdf')
            
            email.send()
            logger.info(f"Email enviado exitosamente a {email_address} para reporte ID {image_id}")
            return True

        except SkinImage.DoesNotExist:
            logger.error(f"No se encontró la imagen con ID {image_id} o no está procesada")
            raise ValidationError("El reporte solicitado no existe o no está listo")
        
        except Exception as e:
            logger.error(f"Error al enviar email para reporte ID {image_id}: {str(e)}")
            return False


def send_report_email(image_id, email_address):
    """
    Función de conveniencia para enviar reportes por email.
    Mantiene la interfaz existente para compatibilidad.
    """
    return EmailReportSender.send_report(image_id, email_address)
