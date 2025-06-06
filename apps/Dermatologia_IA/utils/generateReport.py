# apps/Dermatologia_IA/utils/generateReport.py

"""
  Generación de reportes PDF para análisis dermatológicos.
  Este módulo contiene funciones para construir secciones del reporte,
  generar el PDF y manejar errores durante el proceso.
"""

import os

from django.conf import settings
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportlabImage

from apps.Dermatologia_IA.models import SkinImage
from utils.logger import logger


def _build_patient_section(patient, skin_image, styles):
    """Construye la sección de datos del paciente para el PDF."""
    normal = styles['Normal']
    h2 = styles['h2']
    h3 = styles['h3']
    italic = styles['Italic']
    story = [
        Paragraph("Datos del Paciente e Imagen:", h2),
        Paragraph(f"<b>ID de Imagen:</b> {skin_image.id}", normal),
    ]
    if hasattr(patient, 'get_full_name'):
        story.append(Paragraph(f"<b>Nombre:</b> {patient.get_full_name()}", normal))
    if patient.dni:
        story.append(Paragraph(f"<b>DNI:</b> {patient.dni}", normal))
    if patient.phone:
        story.append(Paragraph(f"<b>Teléfono:</b> {patient.phone}", normal))
    if patient.email:
        story.append(Paragraph(f"<b>Correo Electrónico:</b> {patient.email}", normal))
    if skin_image.uploaded_at:
        story.append(
            Paragraph(
                f"<b>Fecha de Análisis:</b> {skin_image.uploaded_at.strftime('%Y-%m-%d %H:%M')}",
                normal,
            )
        )
    if patient.age_approx is not None:
        story.append(Paragraph(f"<b>Edad Aproximada:</b> {patient.age_approx}", normal))
    if patient.sex:
        story.append(Paragraph(f"<b>Sexo:</b> {patient.get_sex_display()}", normal))
    if skin_image.anatom_site_general:
        story.append(
            Paragraph(
                f"<b>Localización Anatómica:</b> {skin_image.get_anatom_site_general_display()}",
                normal,
            )
        )
    story += [Spacer(1, 0.2 * inch)]
    return story

def _build_image_section(skin_image, styles):
    """Construye la sección de imágenes (original y Grad-CAM) para el PDF."""
    h3 = styles['h3']
    italic = styles['Italic']
    story = []
    img_path = skin_image.image.path
    if os.path.exists(img_path):
        story.append(Paragraph("Imagen Analizada:", h3))
        try:
            img = ReportlabImage(img_path, width=2.5 * inch, height=2.5 * inch)
            img.hAlign = 'CENTER'
            story += [img, Spacer(1, 0.1 * inch)]
        except Exception as e:
            logger.warning('generate_report', f'Error al cargar imagen original: {e}')
            story.append(Paragraph("<i>Error al cargar imagen original.</i>", italic))
    else:
        story.append(Paragraph("<i>Imagen original no encontrada.</i>", italic))
    grad_fs = None
    if skin_image.gradcam_path:
        try:
            rel = skin_image.gradcam_path.replace(settings.MEDIA_URL, '').lstrip('/')
            grad_fs = os.path.join(settings.MEDIA_ROOT, rel)
        except Exception as e:
            logger.warning('generate_report', f'Error al obtener ruta Grad-CAM: {e}')
            grad_fs = None
    if grad_fs and os.path.exists(grad_fs):
        story.append(Paragraph("Mapa de Calor (Grad-CAM):", h3))
        try:
            grad_img = ReportlabImage(grad_fs, width=2.5 * inch, height=2.5 * inch)
            grad_img.hAlign = 'CENTER'
            story += [grad_img, Spacer(1, 0.2 * inch)]
        except Exception as e:
            logger.warning('generate_report', f'Error al cargar Grad-CAM: {e}')
            story.append(Paragraph("<i>Error al cargar Grad-CAM.</i>", italic))
    else:
        story.append(Paragraph("<i>Mapa de calor no disponible.</i>", italic))
    return story

def _build_diagnosis_section(skin_image, styles):
    """Construye la sección de diagnóstico y reporte IA para el PDF."""
    h2 = styles['h2']
    normal = styles['Normal']
    story = [Paragraph("Diagnóstico Preliminar (Basado en IA):", h2)]
    story.append(Paragraph(f"<b>Condición Sugerida:</b> {skin_image.condition or 'No determinada'}", normal))
    if skin_image.confidence is not None:
        valor_conf = skin_image.confidence
        porcentaje = valor_conf * 100 if valor_conf <= 1 else valor_conf
        story.append(Paragraph(f"<b>Confianza del Modelo:</b> {porcentaje:.2f}%", normal))
    story += [Spacer(1, 0.2 * inch)]
    story.append(Paragraph("Reporte (Generado por IA):", h2))
    report = (skin_image.ai_report or "No disponible.").replace('**', '').strip()
    story.append(Paragraph(report.replace('\n', '<br/>'), normal))
    story += [Spacer(1, 0.2 * inch)]
    story.append(Paragraph("Tratamiento (Generado por IA):", h2))
    treat = (skin_image.ai_treatment or "No disponible.").replace('**', '').strip()
    story.append(Paragraph(treat.replace('\n', '<br/>'), normal))
    story += [Spacer(1, 0.3 * inch)]
    return story

def generate_report(image_id):
    """
    Genera un reporte PDF para una imagen dermatológica procesada.
    """
    logger.info('generate_report', f'Generando reporte PDF para imagen ID {image_id}')
    try:
        skin_image = SkinImage.objects.get(id=image_id, processed=True)
        patient = skin_image.patient
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_dermatologico_{image_id}.pdf"'
        doc = SimpleDocTemplate(
            response,
            pagesize=letter,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )
        styles = getSampleStyleSheet()
        h1 = styles['h1']
        story = [
            Paragraph("Reporte de Análisis Dermatológico Preliminar", h1),
            Spacer(1, 0.2 * inch),
        ]
        # Secciones del PDF
        story.extend(_build_patient_section(patient, skin_image, styles))
        story.extend(_build_image_section(skin_image, styles))
        story.extend(_build_diagnosis_section(skin_image, styles))
        doc.build(story)
        logger.success('generate_report', f'Reporte PDF generado correctamente para imagen ID {image_id}')
        return response
    except SkinImage.DoesNotExist:
        logger.error('generate_report', f'No existe imagen procesada con ID {image_id}')
        return None
    except Exception as e:
        logger.error('generate_report', f'Error crítico al generar PDF para ID {image_id}: {e}')
        return None
