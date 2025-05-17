import os
import traceback

import cv2
import google.generativeai as genai
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.models import load_model

from core.Dermatologia_IA.forms.form_report_user_IA import SkinImageForm
from core.Dermatologia_IA.models import SkinImage

# --- Configuración de Rutas y Carga de Componentes de IA ---
RESULTS_DIR = os.path.join(settings.BASE_DIR, 'Entrenamiento_IA', 'RESULTADOS_DEL_MODELO_ENTRENADO')
MODEL_FILENAME = 'Modelo_IA_Entrenada.keras'
PREPROCESSOR_FILENAME = 'metadata_preprocessor.joblib'
MODEL_PATH = os.path.join(RESULTS_DIR, MODEL_FILENAME)
PREPROCESSOR_PATH = os.path.join(RESULTS_DIR, PREPROCESSOR_FILENAME)

print(f"DEBUG: settings.BASE_DIR es: {settings.BASE_DIR}")
print(f"DEBUG: RESULTADOS_DEL_MODELO_ENTRENADO en: {RESULTS_DIR}")
print(f"DEBUG: Ruta modelo: {MODEL_PATH}")
print(f"DEBUG: Ruta preprocesador: {PREPROCESSOR_PATH}")

all_possible_classes_in_data = ['AK', 'BCC', 'BKL', 'DF', 'MEL', 'NV', 'SCC', 'VASC']
condition_classes = sorted(all_possible_classes_in_data)
index_to_class = {i: name for i, name in enumerate(condition_classes)}

print(f"Clases esperadas por el modelo: {condition_classes}")
print(f"Mapeo índice a clase: {index_to_class}")

# --- Carga de Modelo Keras ---
keras_model = None
if os.path.exists(MODEL_PATH):
  try:
    keras_model = load_model(MODEL_PATH)
    print(f"Modelo Keras cargado correctamente desde: {MODEL_PATH}")
  except Exception as e:
    print(f"Error crítico al cargar el modelo Keras desde {MODEL_PATH}: {e}")
    traceback.print_exc()
    keras_model = None
else:
  print(f"Error crítico: No se encontró el archivo del modelo Keras en {MODEL_PATH}")
  keras_model = None

# --- Carga del Preprocesador de Metadatos ---
metadata_preprocessor = None
if os.path.exists(PREPROCESSOR_PATH):
  try:
    metadata_preprocessor = joblib.load(PREPROCESSOR_PATH)
    print(f"Preprocesador de metadatos cargado desde: {PREPROCESSOR_PATH}")
    # Verificación inicial
    metadata_cols = ['age_approx', 'sex', 'anatom_site_general', 'dataset']
    dummy_metadata = pd.DataFrame({
      'age_approx': [50], 'sex': ['male'], 'anatom_site_general': ['unknown'], 'dataset': ['ISIC']
    })[metadata_cols]
    dummy_metadata['age_approx'] = pd.to_numeric(dummy_metadata['age_approx'], errors='coerce').fillna(50)
    for col in ['sex', 'anatom_site_general', 'dataset']:
      dummy_metadata[col] = dummy_metadata[col].astype(str).fillna('unknown')
    processed_shape = metadata_preprocessor.transform(dummy_metadata).shape[1]
    print(f"DEBUG: Dimensión de metadatos procesados: {processed_shape}")
  except Exception as e:
    print(f"Error crítico al cargar o verificar el preprocesador desde {PREPROCESSOR_PATH}: {e}")
    traceback.print_exc()
    metadata_preprocessor = None
else:
  print(f"Error crítico: No se encontró el preprocesador en {PREPROCESSOR_PATH}")
  metadata_preprocessor = None

# --- Configuración de Gemini AI ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
gemini_model = None
if GEMINI_API_KEY:
  try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    gemini_model.generate_content("Hello", generation_config=genai.types.GenerationConfig(max_output_tokens=10))
    print("Gemini AI configurado y conexión exitosa.")
  except Exception as e:
    print(f"Error al configurar o conectar con Gemini AI: {e}")
    traceback.print_exc()
    gemini_model = None
else:
  print("ADVERTENCIA: GEMINI_API_KEY no definida. Generación de reportes limitada.")
  gemini_model = None


class ReportListView(ListView):
  model = SkinImage
  template_name = 'Dermatologia_IA/report_list.html'
  context_object_name = 'reports'

  def get_queryset(self):
    return SkinImage.objects.filter(processed=True)  # Filter processed reports only


class ReportDetailView(DetailView):
  model = SkinImage
  template_name = 'Dermatologia_IA/results.html'  # Reusing your existing template
  context_object_name = 'skin_image'
  # Add this line to specify the URL kwarg to use for lookup
  pk_url_kwarg = 'image_id'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['show_actions'] = False  # Hide action buttons in detail view
    return context


# --- Clase AIProcessor ---
class AIProcessor:
  """Clase para manejar la lógica de procesamiento con IA"""

  @staticmethod
  def preprocess_image_for_model(image_path):
    try:
      img = cv2.imread(image_path)
      if img is None:
        raise ValueError(f"No se pudo cargar la imagen desde: {image_path}")
      img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
      img_resized = cv2.resize(img_rgb, (224, 224))
      img_preprocessed = preprocess_input(img_resized)
      img_array = np.expand_dims(img_preprocessed, axis=0)
      return img_array, img_rgb
    except Exception as e:
      print(f"Error crítico al preprocesar la imagen {image_path}: {e}")
      traceback.print_exc()
      return None, None

  @staticmethod
  def preprocess_metadata_for_model(metadata_dict, fitted_preprocessor):
    if not fitted_preprocessor:
      print("Error crítico: Preprocesador de metadatos no disponible")
      return None
    try:
      expected_cols = ['age_approx', 'sex', 'anatom_site_general', 'dataset']
      metadata_df = pd.DataFrame([metadata_dict])[expected_cols]
      metadata_df['age_approx'] = pd.to_numeric(metadata_df['age_approx'], errors='coerce').fillna(50)
      for col in ['sex', 'anatom_site_general', 'dataset']:
        metadata_df[col] = metadata_df[col].astype(str).fillna('unknown')
      processed_metadata = fitted_preprocessor.transform(metadata_df)
      return processed_metadata
    except Exception as e:
      print(f"Error crítico al procesar metadatos: {e}")
      traceback.print_exc()
      return None

  @staticmethod
  def calculate_gradcam_image_only(img_array, full_model, actual_pred_index):
    try:
      base_model_name = 'resnet50_base'
      base_model_layer = full_model.get_layer(base_model_name)
      last_conv_layer = None
      last_conv_layer_name = None
      for layer in reversed(base_model_layer.layers):
        if isinstance(layer, (tf.keras.layers.Conv2D, tf.keras.layers.DepthwiseConv2D)):
          last_conv_layer = layer
          last_conv_layer_name = layer.name
          break
      if not last_conv_layer:
        raise ValueError(f"No se encontró capa convolucional en {base_model_name}")

      image_only_grad_model = tf.keras.Model(
        inputs=base_model_layer.input,
        outputs=[last_conv_layer.output, base_model_layer.output]
      )

      with tf.GradientTape() as tape:
        conv_output_value, base_output_value = image_only_grad_model(tf.cast(img_array, tf.float32), training=False)
        tape.watch(conv_output_value)
        output_for_grads = tf.reduce_sum(base_output_value)
      grads = tape.gradient(output_for_grads, conv_output_value)
      if grads is None:
        raise ValueError("Gradientes no calculados")

      pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
      heatmap = conv_output_value[0] @ pooled_grads[..., tf.newaxis]
      heatmap = tf.squeeze(tf.maximum(heatmap, 0))
      max_val = tf.reduce_max(heatmap)
      heatmap = heatmap / max_val if max_val > 0 else heatmap
      return heatmap.numpy(), last_conv_layer_name
    except Exception as e:
      print(f"Error crítico al calcular Grad-CAM: {e}")
      traceback.print_exc()
      return None, last_conv_layer_name if 'last_conv_layer_name' in locals() else "Desconocida"

  @staticmethod
  def generate_ai_content(condition):
    default_report = f"Descripción no disponible para {condition}. Consulte a un dermatólogo."
    default_treatment = f"Tratamiento no disponible para {condition}. Busque atención médica."
    if not gemini_model:
      print(f"Gemini AI no configurado. Usando valores por defecto para {condition}.")
      return default_report, default_treatment
    try:
      report_prompt = f"Describe brevemente (máx. 500 caracteres) la condición {condition}: qué es, síntomas, causas. Consulta profesional requerida."
      treatment_prompt = f"Recomendaciones breves (máx. 500 caracteres) para {condition}: tratamientos generales, cuidados. Consulta dermatólogo esencial."
      config = genai.types.GenerationConfig(max_output_tokens=150, temperature=0.7)
      report_response = gemini_model.generate_content(report_prompt, generation_config=config)
      treatment_response = gemini_model.generate_content(treatment_prompt, generation_config=config)
      ai_report = report_response.text.strip() if hasattr(report_response, 'text') else default_report
      ai_treatment = treatment_response.text.strip() if hasattr(treatment_response, 'text') else default_treatment
      return ai_report[:500], ai_treatment[:500]
    except Exception as e:
      print(f"Error crítico al generar contenido con Gemini AI para {condition}: {e}")
      traceback.print_exc()
      return default_report, default_treatment


# --- Clase UploadImageView ---
class UploadImageView(View):
  template_name = 'Dermatologia_IA/upload.html'

  def get(self, request):
    form = SkinImageForm()
    return render(request, self.template_name, {'form': form})

  def post(self, request):
    form = SkinImageForm(request.POST, request.FILES)
    if form.is_valid():
      try:
        if keras_model is None or metadata_preprocessor is None:
          print("Error crítico: Modelo o preprocesador no cargados")
          return JsonResponse({
            'success': False,
            'error': 'Sistema de análisis no disponible. Contacte al administrador.'
          })
        skin_image = form.save(commit=False)
        skin_image.processed = False
        skin_image.condition = None
        skin_image.location = skin_image.get_anatom_site_general_display()
        skin_image.confidence = None
        skin_image.ai_report = ""
        skin_image.ai_treatment = ""
        skin_image.gradcam_path = None
        skin_image.save()
        print(f"Imagen guardada con ID: {skin_image.id}")
        process_url = reverse('dermatology:process_image', kwargs={'image_id': skin_image.id})
        return JsonResponse({'success': True, 'redirect_url': process_url})
      except Exception as e:
        print(f"Error crítico al guardar imagen y metadatos: {e}")
        traceback.print_exc()
        return JsonResponse({
          'success': False,
          'error': 'Error interno al guardar los datos. Intente nuevamente o contacte soporte.'
        })
    else:
      print(f"Error de formulario: {form.errors.as_json()}")
      return JsonResponse({
        'success': False,
        'error': 'Corrija los errores del formulario.',
        'form_errors': form.errors.as_json()
      })


# --- Clase ProcessImageView ---
class ProcessImageView(DetailView):
  model = SkinImage
  template_name = 'Dermatologia_IA/results.html'
  context_object_name = 'skin_image'
  pk_url_kwarg = 'image_id'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    skin_image = self.object

    if skin_image.processed:
      print(f"Mostrando resultados procesados para ID {skin_image.id}")
      context.update({
        'condition': skin_image.condition or "No determinado",
        'location': skin_image.location or skin_image.get_anatom_site_general_display() or "No especificado",
        'confidence': skin_image.confidence,
        'report': skin_image.ai_report or "No disponible",
        'treatment': skin_image.ai_treatment or "No disponible",
        'gradcam_path': skin_image.gradcam_path,
        'age_approx': skin_image.age_approx,
        'sex': skin_image.get_sex_display() or "No especificado",
        'anatom_site_general': skin_image.get_anatom_site_general_display() or "No especificado",
        'uploaded_at': skin_image.uploaded_at,
        'image_url': skin_image.image.url if skin_image.image else None,
      })
      return context

    print(f"Iniciando procesamiento para ID {skin_image.id}")
    context['processing_now'] = True

    try:
      if keras_model is None or metadata_preprocessor is None:
        raise Exception("Sistema de análisis no disponible")

      image_path = skin_image.image.path
      if not os.path.exists(image_path):
        raise FileNotFoundError(f"Imagen no encontrada en {image_path}")

      img_array, original_img_rgb = AIProcessor.preprocess_image_for_model(image_path)
      if img_array is None or original_img_rgb is None:
        raise ValueError("Fallo al preprocesar la imagen")

      metadata_dict = {
        'age_approx': skin_image.age_approx, 'sex': skin_image.sex,
        'anatom_site_general': skin_image.anatom_site_general, 'dataset': 'ISIC'
      }
      metadata_processed = AIProcessor.preprocess_metadata_for_model(metadata_dict, metadata_preprocessor)
      if metadata_processed is None:
        raise ValueError("Fallo al preprocesar metadatos")

      img_input = tf.constant(img_array, dtype=tf.float32)
      meta_input = tf.constant(metadata_processed, dtype=tf.float32)
      prediction = keras_model.predict([img_input, meta_input], verbose=0)

      if prediction.shape != (1, len(condition_classes)):
        raise ValueError(f"Predicción con forma inválida: {prediction.shape}")

      condition_pred_probs = prediction[0]
      condition_index = np.argmax(condition_pred_probs)
      predicted_condition = index_to_class.get(condition_index, "Condición desconocida")
      confidence = float(condition_pred_probs[condition_index] * 100)
      skin_image.condition = predicted_condition
      skin_image.confidence = confidence

      try:
        heatmap_np_0_1, layer_name_used = AIProcessor.calculate_gradcam_image_only(img_array, keras_model,
                                                                                   condition_index)
        if heatmap_np_0_1 is not None:
          target_h, target_w = original_img_rgb.shape[0], original_img_rgb.shape[1]
          heatmap_resized = cv2.resize(heatmap_np_0_1, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
          heatmap_uint8 = np.uint8(255 * heatmap_resized)
          heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
          original_img_bgr = cv2.cvtColor(original_img_rgb, cv2.COLOR_RGB2BGR)
          if original_img_bgr.dtype != np.uint8:
            original_img_bgr = cv2.normalize(original_img_bgr, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
          superimposed_img = cv2.addWeighted(original_img_bgr, 0.6, heatmap_colored, 0.4, 0)
          gradcam_filename = f'gradcam_{skin_image.id}.jpg'
          gradcam_dir = os.path.join(settings.MEDIA_ROOT, 'gradcam_images')
          os.makedirs(gradcam_dir, exist_ok=True)
          gradcam_path_fs = os.path.join(gradcam_dir, gradcam_filename)
          if cv2.imwrite(gradcam_path_fs, superimposed_img):
            skin_image.gradcam_path = os.path.join(settings.MEDIA_URL, 'gradcam_images', gradcam_filename).replace("\\",
                                                                                                                   "/")
          else:
            raise Exception("Fallo al guardar Grad-CAM")
        else:
          messages.warning(self.request, "No se pudo generar el mapa de calor (Grad-CAM).")
      except Exception as e_gradcam:
        print(f"Error crítico al generar Grad-CAM: {e_gradcam}")
        traceback.print_exc()
        messages.warning(self.request, "No se pudo generar el mapa de calor.")
        skin_image.gradcam_path = None

      if predicted_condition:
        ai_report, ai_treatment = AIProcessor.generate_ai_content(predicted_condition)
        skin_image.ai_report = ai_report
        skin_image.ai_treatment = ai_treatment
        if not gemini_model:
          messages.info(self.request, "Generación de detalles por IA no activa.")
      else:
        skin_image.ai_report = "Reporte no generado."
        skin_image.ai_treatment = "Tratamiento no generado."

      skin_image.processed = True
      skin_image.save()
      messages.success(self.request, f"Análisis completado: {predicted_condition}")

      context.update({
        'condition': predicted_condition,
        'location': skin_image.location or skin_image.get_anatom_site_general_display(),
        'confidence': confidence,
        'report': skin_image.ai_report,
        'treatment': skin_image.ai_treatment,
        'gradcam_path': skin_image.gradcam_path,
        'age_approx': skin_image.age_approx,
        'sex': skin_image.get_sex_display(),
        'anatom_site_general': skin_image.get_anatom_site_general_display(),
        'uploaded_at': skin_image.uploaded_at,
        'image_url': skin_image.image.url if skin_image.image else None,
      })

    except FileNotFoundError as e:
      print(f"Error crítico: Imagen no encontrada - {e}")
      traceback.print_exc()
      messages.error(self.request, "No se encontró la imagen. Suba la imagen nuevamente.")
      context['error'] = "Archivo de imagen no encontrado."
    except ValueError as e:
      print(f"Error crítico de datos: {e}")
      traceback.print_exc()
      messages.error(self.request, "Error en los datos. Verifique la información ingresada.")
      context['error'] = "Error en los datos."
    except Exception as e:
      print(f"Error crítico inesperado: {e}")
      traceback.print_exc()
      messages.error(self.request, "Error durante el procesamiento. Contacte soporte.")
      context['error'] = "Error inesperado."

    context.pop('processing_now', None)
    return context
