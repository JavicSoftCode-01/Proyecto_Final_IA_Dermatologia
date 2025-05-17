# core/Dermatologia_IA/utils/generateReport.py

import os

from django.conf import settings
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportlabImage

from core.Dermatologia_IA.models import SkinImage


def generate_report(image_id):
  """
  Genera un reporte PDF para una imagen dermatológica procesada.
  Args:
      image_id (int): ID de la imagen en la base de datos.
  Returns:
      HttpResponse: Respuesta con el PDF generado o None si hay un error.
  """
  try:
    # Obtener la instancia de SkinImage
    skin_image = SkinImage.objects.get(id=image_id, processed=True)

    # Crear una respuesta HttpResponse con tipo de contenido PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_dermatologico_{image_id}.pdf"'

    # Configurar el documento PDF con ReportLab
    doc = SimpleDocTemplate(response, pagesize=letter,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    h1_style = styles['h1']
    h2_style = styles['h2']
    h3_style = styles['h3']
    normal_style = styles['Normal']
    normal_style.wordWrap = 'CJK'
    italic_style = styles['Italic']

    # Construir el contenido del PDF
    story = [
      Paragraph("Reporte de Análisis Dermatológico Preliminar", h1_style),
      Spacer(1, 0.2 * inch),
      Paragraph("Datos de la Imagen/Paciente:", h2_style),
      Paragraph(f"<b>ID de Imagen:</b> {skin_image.id}", normal_style)
    ]

    if skin_image.uploaded_at:
      story.append(
        Paragraph(f"<b>Fecha de Análisis:</b> {skin_image.uploaded_at.strftime('%Y-%m-%d %H:%M')}", normal_style))
    if skin_image.age_approx is not None:
      story.append(Paragraph(f"<b>Edad Aproximada:</b> {skin_image.age_approx}", normal_style))
    if skin_image.sex:
      story.append(Paragraph(f"<b>Sexo:</b> {skin_image.get_sex_display()}", normal_style))
    if skin_image.anatom_site_general:
      story.append(
        Paragraph(f"<b>Localización Anatómica:</b> {skin_image.get_anatom_site_general_display()}", normal_style))

    story.append(Spacer(1, 0.2 * inch))

    # Imagen Original
    img_path = skin_image.image.path
    if os.path.exists(img_path):
      story.append(Paragraph("Imagen Analizada:", h3_style))
      try:
        img = ReportlabImage(img_path, width=2.5 * inch, height=2.5 * inch)
        img.hAlign = 'CENTER'
        story.append(img)
        story.append(Spacer(1, 0.1 * inch))
      except Exception as img_err:
        print(f"Error al cargar imagen original para PDF {image_id}: {img_err}")
        story.append(Paragraph("<i>Error al cargar imagen original.</i>", italic_style))
    else:
      print(f"PDF Gen: Imagen original NO encontrada en ruta: {img_path}")
      story.append(Paragraph("<i>Imagen original no encontrada.</i>", italic_style))

    # Grad-CAM
    gradcam_fs_path = None
    if skin_image.gradcam_path:
      print(f"PDF Gen: URL Grad-CAM encontrada en DB: {skin_image.gradcam_path}")
      try:
        relative_path = skin_image.gradcam_path.replace(settings.MEDIA_URL, '', 1).lstrip('/')
        gradcam_fs_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        print(f"PDF Gen: Ruta Grad-CAM calculada: {gradcam_fs_path}")
      except Exception as e:
        print(f"PDF Gen: Error al convertir URL GradCAM a ruta de archivo: {e}")
        gradcam_fs_path = None

    if gradcam_fs_path and os.path.exists(gradcam_fs_path):
      story.append(Paragraph("Mapa de Calor (Grad-CAM):", h3_style))
      try:
        grad_img = ReportlabImage(gradcam_fs_path, width=2.5 * inch, height=2.5 * inch)
        grad_img.hAlign = 'CENTER'
        story.append(grad_img)
        story.append(Spacer(1, 0.2 * inch))
        print(f"PDF Gen: Imagen Grad-CAM añadida desde {gradcam_fs_path}")
      except Exception as grad_err:
        print(f"Error al cargar imagen Grad-CAM para PDF {image_id} desde {gradcam_fs_path}: {grad_err}")
        story.append(Paragraph(f"<i>Error al cargar imagen Grad-CAM desde {gradcam_fs_path}.</i>", italic_style))
    elif skin_image.gradcam_path:
      print(f"PDF Gen: Archivo Grad-CAM NO encontrado en ruta calculada: {gradcam_fs_path}")
      story.append(Paragraph("<i>Imagen Grad-CAM no encontrada en el servidor.</i>", italic_style))
    else:
      story.append(Paragraph("<i>Mapa de calor no disponible.</i>", italic_style))

    # Diagnóstico Preliminar
    story.append(Paragraph("Diagnóstico Preliminar (Basado en IA):", h2_style))
    story.append(Paragraph(f"<b>Condición Sugerida:</b> {skin_image.condition or 'No determinada'}", normal_style))
    if skin_image.confidence is not None:
      story.append(Paragraph(f"<b>Confianza del Modelo:</b> {skin_image.confidence:.2f}%", normal_style))
    if skin_image.location and skin_image.location != "No determinado":
      story.append(Paragraph(f"<b>Ubicación Registrada:</b> {skin_image.location}", normal_style))

    story.append(Spacer(1, 0.2 * inch))

    # Reporte Detallado IA
    story.append(Paragraph("Reporte (Generado por IA):", h2_style))
    report_text = (skin_image.ai_report or "No disponible.").replace('**', '').strip()
    story.append(Paragraph(report_text.replace('\n', '<br/>'), normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # Tratamiento IA
    story.append(Paragraph("Tratamiento (Generado por IA):", h2_style))
    treatment_text = (skin_image.ai_treatment or "No disponible.").replace('**', '').strip()
    story.append(Paragraph(treatment_text.replace('\n', '<br/>'), normal_style))
    story.append(Spacer(1, 0.3 * inch))

    # Aviso Importante
    story.append(Paragraph("<u>Aviso Importante:</u>", h3_style))
    story.append(Paragraph(
      "Este reporte se genera mediante inteligencia artificial. Es una herramienta de apoyo y <b>NO sustit Hannahs sustituye el diagnóstico ni la consulta con un médico dermatólogo cualificado</b>. Los resultados son preliminares y deben ser confirmados por un profesional de la salud. Consulte siempre a su médico.",
      normal_style
    ))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
      "<i>No tome decisiones médicas basándose únicamente en este reporte.</i>",
      italic_style
    ))

    # Construir el documento PDF
    doc.build(story)
    print(f"PDF generado correctamente para imagen ID {image_id}")
    return response

  except SkinImage.DoesNotExist:
    print(f"Error: No se encontró la imagen con ID {image_id} o no está procesada.")
    return None
  except Exception as e:
    print(f"Error crítico al generar el PDF para imagen ID {image_id}: {e}")
    import traceback
    traceback.print_exc()
    return None
