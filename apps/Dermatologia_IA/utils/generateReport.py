"""
Generación de reportes PDF profesionales para análisis dermatológicos.
Versión corregida y optimizada para una sola página con diseño personalizado.
"""

import os
import traceback

from django.conf import settings
from django.http import HttpResponse
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
  SimpleDocTemplate, Paragraph, Spacer, Image as ReportlabImage,
  Table, TableStyle
)

from apps.Dermatologia_IA.models import SkinImage
from utils.logger import logger

LOGO_URL = 'https://img.freepik.com/vector-premium/clinica-dermatologia-cabello-icono-crecimiento-foliculo-emblema_8071-62148.jpg'
SIGNATURE_URL = 'https://img.freepik.com/vector-premium/firma-manual-documentos-sobre-fondo-blanco-ilustracion-vectorial-letras-caligrafia-dibujadas-mano_81863-11806.jpg'

COLORS = {
  'primary': HexColor('#0D6EFD'),
  'secondary': HexColor('#4A90A4'),
  'text_dark': HexColor('#2D3748'),
  'text_light': HexColor('#4A5568'),
  'background': HexColor('#F7FAFC'),
  'border': HexColor('#E2E8F0'),
}


def _create_custom_styles():
  styles = getSampleStyleSheet()
  styles.add(ParagraphStyle(
    name='SectionHeader', parent=styles['Heading2'], fontSize=14, textColor=COLORS['primary'],
    spaceBefore=10, spaceAfter=6, fontName='Helvetica-Bold'
  ))
  styles.add(ParagraphStyle(
    name='SubsectionHeader', parent=styles['Heading3'], fontSize=11, textColor=COLORS['secondary'],
    spaceBefore=14, spaceAfter=8, fontName='Helvetica-Bold', alignment=TA_CENTER
  ))
  styles.add(ParagraphStyle(
    name='CustomNormal', parent=styles['Normal'], fontSize=9.5, textColor=COLORS['text_dark'],
    spaceAfter=6, leading=12, fontName='Helvetica'
  ))
  styles.add(ParagraphStyle(
    name='HighlightInfo', parent=styles['Normal'], fontSize=9, textColor=COLORS['text_dark'],
    spaceAfter=8, leftIndent=10, fontName='Helvetica', backColor=COLORS['background'],
    borderWidth=1, borderColor=COLORS['border'], borderPadding=8, leading=12
  ))
  styles.add(ParagraphStyle(
    name='ImageCaption', parent=styles['Normal'], fontSize=7.5, textColor=COLORS['text_light'],
    alignment=TA_CENTER, fontName='Helvetica-Oblique'
  ))
  styles.add(ParagraphStyle(
    name='DoctorName', parent=styles['Normal'], fontSize=10, textColor=COLORS['text_dark'],
    alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=4
  ))
  return styles


def _build_header(canvas, doc):
  canvas.saveState()
  canvas.setFillColor(COLORS['primary'])
  canvas.rect(0, doc.height + doc.topMargin - (1 * inch), doc.width + doc.leftMargin + doc.rightMargin, 1 * inch,
              stroke=0, fill=1)

  try:
    logo = ReportlabImage(LOGO_URL, width=0.8 * inch, height=0.8 * inch, kind='proportional')
    logo.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - (0.9 * inch))
  except Exception as e:
    logger.warning('generate_report', f'No se pudo cargar el logo desde la URL: {e}')
    canvas.setFillColor(white)
    canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - (0.6 * inch), "Logo")

  canvas.setFillColor(white)
  canvas.setFont('Helvetica-Bold', 14)
  canvas.drawString(doc.leftMargin + 1 * inch, doc.height + doc.topMargin - (0.55 * inch),
                    "DERMA IA - Reporte de Análisis Dermatológico")
  canvas.setFont('Helvetica', 9)
  canvas.drawString(doc.leftMargin + 1 * inch, doc.height + doc.topMargin - (0.75 * inch),
                    "javicsoftcode@gmail.com | Tel: +593 99 533 6523")
  canvas.restoreState()


def _build_patient_info_table(patient, skin_image, styles):
  patient_data = [
    [Paragraph('<b>DNI/Cédula</b>', styles['CustomNormal']), patient.dni or 'N/A',
     Paragraph('<b>Localización</b>', styles['CustomNormal']), skin_image.get_anatom_site_general_display() or 'N/A'],
    [Paragraph('<b>Paciente</b>', styles['CustomNormal']),
     patient.get_full_name() if hasattr(patient, 'get_full_name') else 'N/A',
     Paragraph('<b>Sexo</b>', styles['CustomNormal']), patient.get_sex_display() if patient.sex else 'N/A'],
    [Paragraph('<b>Edad</b>', styles['CustomNormal']), f"{patient.age_approx} años" if patient.age_approx else 'N/A',
     Paragraph('<b>Fecha Análisis</b>', styles['CustomNormal']),
     skin_image.uploaded_at.strftime('%d/%m/%Y') if skin_image.uploaded_at else 'N/A'],
  ]

  table = Table(patient_data, colWidths=[1.1 * inch, 2.6 * inch, 1.1 * inch, 2.7 * inch])
  table.setStyle(TableStyle([
    ('GRID', (0, 0), (-1, -1), 0.5, COLORS['border']),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
  ]))
  return table


def _build_images_section(skin_image, styles):
  img_size = 2.2 * inch
  original_content = [Paragraph("Imagen Original", styles['SubsectionHeader'])]
  try:
    img = ReportlabImage(skin_image.image.path, width=img_size, height=img_size, kind='proportional')
    original_content.append(img)
  except Exception:
    original_content.append(Paragraph("Imagen no encontrada.", styles['ImageCaption']))

  gradcam_content = [Paragraph("Grad-CAM", styles['SubsectionHeader'])]
  if skin_image.gradcam_path:
    try:
      rel = skin_image.gradcam_path.replace(settings.MEDIA_URL, '').lstrip('/')
      grad_fs = os.path.join(settings.MEDIA_ROOT, rel)
      if os.path.exists(grad_fs):
        grad_img = ReportlabImage(grad_fs, width=img_size, height=img_size, kind='proportional')
        gradcam_content.append(grad_img)
      else:
        gradcam_content.append(Paragraph("Mapa no disponible.", styles['ImageCaption']))
    except Exception:
      gradcam_content.append(Paragraph("Error al cargar Grad-CAM.", styles['ImageCaption']))
  else:
    gradcam_content.append(Paragraph("Grad-CAM no disponible.", styles['ImageCaption']))

  images_table = Table([[original_content, gradcam_content]], colWidths=[3.75 * inch, 3.75 * inch])
  images_table.setStyle(TableStyle([
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
  ]))
  return [images_table]


def _build_diagnosis_section(skin_image, styles):
  confidence_str = 'N/A'
  if skin_image.confidence is not None:
    confidence_str = f"{skin_image.confidence:.1%}"
  diag_text = f"""
        <b>Condición Identificada:</b> {skin_image.condition or 'No determinada'}<br/>
        <b>Nivel de Confianza de la IA:</b> {confidence_str}
    """
  return [Paragraph(diag_text, styles['CustomNormal'])]


def _build_ai_analysis_section(skin_image, styles):
  story = []
  if skin_image.ai_report:
    story.append(Spacer(1, -0.20 * inch))
    story.append(Paragraph("<b>Análisis Detallado (IA)</b>", styles['SubsectionHeader']))
    report_content = skin_image.ai_report.replace('**', '<b>').replace('\n', '<br/>').strip()
    story.append(Paragraph(report_content, styles['HighlightInfo']))

  if skin_image.ai_treatment:
    story.append(Spacer(1, -0.10 * inch))
    story.append(Paragraph("<b>Sugerencias (IA)</b>", styles['SubsectionHeader']))
    treatment_content = skin_image.ai_treatment.replace('**', '<b>').replace('\n', '<br/>').strip()
    story.append(Paragraph(treatment_content, styles['HighlightInfo']))
  return story


def _build_signature_section(styles):
  try:
    signature_img = ReportlabImage(SIGNATURE_URL, width=1.5 * inch, height=0.75 * inch)
  except Exception as e:
    logger.warning('generate_report', f'No se pudo cargar la firma desde la URL: {e}')
    signature_img = Paragraph("Firma", styles['ImageCaption'])

  # Estructura de la firma con el nombre del doctor debajo
  signature_info = [
    [signature_img],
    [Paragraph("Dr. Sistema DERMA IA", styles['DoctorName'])],
    [Paragraph("Análisis Dermatológico Automatizado | Reg: IA-2025-DERM", styles['ImageCaption'])]
  ]

  signature_table = Table(signature_info, colWidths=[7.5 * inch])
  signature_table.setStyle(TableStyle([
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ('TOPPADDING', (0, 0), (-1, -1), 2),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
  ]))
  return [signature_table]


def _draw_footer_disclaimer(canvas, doc):
  canvas.saveState()
  disclaimer_text = "IMPORTANTE: Este reporte ha sido generado por IA y es una evaluación preliminar. NO sustituye el diagnóstico de un dermatólogo certificado."
  canvas.setFont('Helvetica-Oblique', 7.5)
  canvas.setFillColor(COLORS['text_light'])
  canvas.drawCentredString(doc.width / 2.0 + doc.leftMargin, 0.3 * inch, disclaimer_text)
  canvas.restoreState()


def generate_report(image_id):
  logger.info('generate_report', f'Generando reporte PDF para imagen ID {image_id}')
  try:
    skin_image = SkinImage.objects.get(id=image_id, processed=True)
    patient = skin_image.patient

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_dermatologico_{image_id}.pdf"'

    doc = SimpleDocTemplate(
      response,
      pagesize=letter,
      leftMargin=0.5 * inch, rightMargin=0.5 * inch,
      topMargin=1 * inch,
      bottomMargin=0.15 * inch
    )

    styles = _create_custom_styles()
    story = [Spacer(1, 0.15 * inch), Paragraph("INFORMACIÓN DEL PACIENTE", styles['SectionHeader']),
             _build_patient_info_table(patient, skin_image, styles), Spacer(1, 0.15 * inch),
             Paragraph("IMÁGENES DE ANÁLISIS", styles['SectionHeader'])]

    story.extend(_build_images_section(skin_image, styles))
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("RESULTADOS DEL ANÁLISIS POR IA", styles['SectionHeader']))
    story.extend(_build_diagnosis_section(skin_image, styles))

    story.extend(_build_ai_analysis_section(skin_image, styles))

    story.append(Spacer(1, 0.2 * inch))
    story.extend(_build_signature_section(styles))

    doc.build(story, onFirstPage=_build_header, onLaterPages=_build_header)

    logger.success('generate_report', f'Reporte PDF generado para imagen ID {image_id}')
    return response

  except SkinImage.DoesNotExist:
    logger.error('generate_report', f'No existe imagen procesada con ID {image_id}')
    return None
  except Exception as e:
    error_details = traceback.format_exc()
    logger.error('generate_report', f'Error crítico al generar PDF para ID {image_id}: {e}\n{error_details}')
    return None
