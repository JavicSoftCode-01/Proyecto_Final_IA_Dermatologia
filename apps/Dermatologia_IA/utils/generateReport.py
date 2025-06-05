# apps/Dermatologia_IA/utils/generateReport.py
import os

from django.conf import settings
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportlabImage

from apps.Dermatologia_IA.models import SkinImage


def generate_report(image_id):
  """
  Genera un reporte PDF para una imagen dermatológica procesada.
  Args:
      image_id (int): ID de la imagen en la base de datos.
  Returns:
      HttpResponse: Respuesta con el PDF generado o None si hay un error.
  """
  try:
    # Obtener la instancia de SkinImage (asegurándonos de que esté procesada)
    skin_image = SkinImage.objects.get(id=image_id, processed=True)
    patient = skin_image.patient  # Obtenemos el paciente asociado

    # Crear una respuesta HttpResponse con tipo de contenido PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
      f'attachment; filename="reporte_dermatologico_{image_id}.pdf"'
    )

    # Configurar el documento PDF con ReportLab
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
    h2 = styles['h2']
    h3 = styles['h3']
    normal = styles['Normal']
    normal.wordWrap = 'CJK'
    italic = styles['Italic']

    # Construir contenido
    story = [
      Paragraph("Reporte de Análisis Dermatológico Preliminar", h1),
      Spacer(1, 0.2 * inch),
      Paragraph("Datos del Paciente e Imagen:", h2),
      Paragraph(f"<b>ID de Imagen:</b> {skin_image.id}", normal),
    ]

    # Datos de paciente (ahora a través de patient)
    if patient.first_name or patient.last_name:
      nombre = f"{patient.first_name or ''} {patient.last_name or ''}".strip()
      story.append(Paragraph(f"<b>Nombre:</b> {nombre}", normal))
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
      story.append(
        Paragraph(f"<b>Edad Aproximada:</b> {patient.age_approx}", normal)
      )
    if patient.sex:
      story.append(
        Paragraph(f"<b>Sexo:</b> {patient.get_sex_display()}", normal)
      )
    if skin_image.anatom_site_general:
      story.append(
        Paragraph(
          f"<b>Localización Anatómica:</b> {skin_image.get_anatom_site_general_display()}",
          normal,
        )
      )
    story.append(Spacer(1, 0.2 * inch))

    # Imagen original
    img_path = skin_image.image.path
    if os.path.exists(img_path):
      story.append(Paragraph("Imagen Analizada:", h3))
      try:
        img = ReportlabImage(img_path, width=2.5 * inch, height=2.5 * inch)
        img.hAlign = 'CENTER'
        story.extend([img, Spacer(1, 0.1 * inch)])
      except Exception:
        story.append(Paragraph("<i>Error al cargar imagen original.</i>", italic))
    else:
      story.append(Paragraph("<i>Imagen original no encontrada.</i>", italic))

    # Grad-CAM
    grad_fs = None
    if skin_image.gradcam_path:
      try:
        rel = skin_image.gradcam_path.replace(settings.MEDIA_URL, '').lstrip('/')
        grad_fs = os.path.join(settings.MEDIA_ROOT, rel)
      except Exception:
        grad_fs = None
    if grad_fs and os.path.exists(grad_fs):
      story.append(Paragraph("Mapa de Calor (Grad-CAM):", h3))
      try:
        grad_img = ReportlabImage(grad_fs, width=2.5 * inch, height=2.5 * inch)
        grad_img.hAlign = 'CENTER'
        story.extend([grad_img, Spacer(1, 0.2 * inch)])
      except Exception:
        story.append(Paragraph("<i>Error al cargar Grad-CAM.</i>", italic))
    else:
      story.append(Paragraph("<i>Mapa de calor no disponible.</i>", italic))

    # Diagnóstico preliminar
    story.append(Paragraph("Diagnóstico Preliminar (Basado en IA):", h2))
    story.append(
      Paragraph(
        f"<b>Condición Sugerida:</b> {skin_image.condition or 'No determinada'}",
        normal
      )
    )
    if skin_image.confidence is not None:
      # Convertimos a porcentaje (si confidence está en [0,1], multiplicar por 100)
      valor_conf = skin_image.confidence
      # Si el usuario maneja ya valores en porcentaje, quitar *100
      porcentaje = valor_conf * 100 if valor_conf <= 1 else valor_conf
      story.append(
        Paragraph(
          f"<b>Confianza del Modelo:</b> {porcentaje:.2f}%", normal
        )
      )
    story.append(Spacer(1, 0.2 * inch))

    # Reporte IA
    story.append(Paragraph("Reporte (Generado por IA):", h2))
    report = (skin_image.ai_report or "No disponible.").replace('**', '').strip()
    story.append(Paragraph(report.replace('\n', '<br/>'), normal))
    story.append(Spacer(1, 0.2 * inch))

    # Tratamiento IA
    story.append(Paragraph("Tratamiento (Generado por IA):", h2))
    treat = (skin_image.ai_treatment or "No disponible.").replace('**', '').strip()
    story.append(Paragraph(treat.replace('\n', '<br/>'), normal))
    story.append(Spacer(1, 0.3 * inch))

    # Construir PDF
    doc.build(story)
    return response

  except SkinImage.DoesNotExist:
    return None
  except Exception as e:
    print(f"Error crítico al generar PDF para ID {image_id}: {e}")
    return None
