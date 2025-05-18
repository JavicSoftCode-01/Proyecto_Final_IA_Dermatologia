# core/Dermatologia_IA/views/view_report_user_IA.py
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

all_possible_classes_in_data = ['AK', 'BCC', 'BKL', 'DF', 'MEL', 'NV', 'SCC', 'VASC']
condition_classes = sorted(all_possible_classes_in_data)
index_to_class = {i: name for i, name in enumerate(condition_classes)}

# --- Carga de Modelo Keras y Preprocesador ---
keras_model = load_model(MODEL_PATH) if os.path.exists(MODEL_PATH) else None
metadata_preprocessor = joblib.load(PREPROCESSOR_PATH) if os.path.exists(PREPROCESSOR_PATH) else None

# --- Configuración de Gemini AI ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
gemini_model = None
if GEMINI_API_KEY:
  genai.configure(api_key=GEMINI_API_KEY)
  gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')


class ReportListView(ListView):
  model = SkinImage
  template_name = 'Dermatologia_IA/report_list.html'
  context_object_name = 'reports'

  def get_queryset(self):
    return SkinImage.objects.filter(processed=True)


class ReportDetailView(DetailView):
  model = SkinImage
  template_name = 'Dermatologia_IA/results.html'
  context_object_name = 'skin_image'
  pk_url_kwarg = 'image_id'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['show_actions'] = False
    si = context['skin_image']
    context.update({
      'first_name': si.first_name,
      'last_name': si.last_name,
      'dni': si.dni,
      'phone': si.phone,
      'email': si.email,
    })
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
    """
    Calcula el mapa de calor Grad-CAM para la imagen usando solo la parte de imagen del modelo.

    Args:
        img_array: Array numpy de la imagen preprocesada
        full_model: Modelo completo de keras
        actual_pred_index: Índice de la clase predicha

    Returns:
        Tupla de (heatmap, nombre_capa) o (None, nombre_capa) si hay error
    """
    try:
      print(f"Iniciando cálculo de Grad-CAM para clase: {actual_pred_index}")
      # Obtener la capa base del modelo ResNet50
      try:
        base_model_name = 'resnet50_base'
        base_model_layer = full_model.get_layer(base_model_name)
        print(f"Modelo base encontrado: {base_model_name}")
      except Exception as e:
        print(f"Error al obtener la capa base '{base_model_name}': {e}")
        # Intentar con otra posible capa base si hay error
        base_model_names = ['resnet', 'base_model', 'cnn_base']
        for name in base_model_names:
          try:
            base_model_layer = full_model.get_layer(name)
            base_model_name = name
            print(f"Modelo base alternativo encontrado: {base_model_name}")
            break
          except:
            continue
        else:
          # Si llegamos aquí, no encontramos ninguna capa base
          raise ValueError("No se pudo encontrar una capa base válida en el modelo")

      # Encontrar la última capa convolucional
      last_conv_layer = None
      last_conv_layer_name = None
      for layer in reversed(base_model_layer.layers):
        if isinstance(layer, (tf.keras.layers.Conv2D, tf.keras.layers.DepthwiseConv2D)):
          last_conv_layer = layer
          last_conv_layer_name = layer.name
          print(f"Última capa convolucional encontrada: {last_conv_layer_name}")
          break

      if not last_conv_layer:
        raise ValueError(f"No se encontró capa convolucional en {base_model_name}")

      # Crear modelo para extraer características y salida de la última capa convolucional
      print("Creando modelo para Grad-CAM...")
      image_only_grad_model = tf.keras.Model(
        inputs=base_model_layer.input,
        outputs=[last_conv_layer.output, base_model_layer.output]
      )

      # Calcular gradientes
      print("Calculando gradientes...")
      with tf.GradientTape() as tape:
        conv_output_value, base_output_value = image_only_grad_model(tf.cast(img_array, tf.float32), training=False)
        tape.watch(conv_output_value)

        # Usar el índice correcto para la clase predicha o sumar todas
        if actual_pred_index >= 0:
          output_for_grads = base_output_value[:, actual_pred_index]
        else:
          output_for_grads = tf.reduce_sum(base_output_value)

      # Obtener gradientes
      grads = tape.gradient(output_for_grads, conv_output_value)
      if grads is None:
        raise ValueError("Gradientes no calculados")

      # Procesar gradientes para generar heatmap
      print("Generando heatmap...")
      pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
      heatmap = tf.matmul(conv_output_value[0], pooled_grads[..., tf.newaxis])
      heatmap = tf.squeeze(heatmap)
      heatmap = tf.maximum(heatmap, 0)  # ReLU para mantener solo activaciones positivas

      # Normalizar heatmap a [0,1]
      max_val = tf.reduce_max(heatmap)
      if max_val > 0:
        heatmap = heatmap / max_val

      # Convertir a numpy para su uso
      heatmap_np = heatmap.numpy()
      print(
        f"Heatmap generado exitosamente. Shape: {heatmap_np.shape}, Rango: [{np.min(heatmap_np)}, {np.max(heatmap_np)}]")

      return heatmap_np, last_conv_layer_name

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
      report_prompt = f"Describe brevemente (máx. 500 caracteres) la condición {condition}: qué es, síntomas, causas. (Hazte pasar como un doctor real con una especialidad en desmatología)"
      treatment_prompt = f"Recomendaciones breves (máx. 500 caracteres) para la condición {condition}: tratamientos generales, cuidados, pastillas para tomar o cremas para aplicar en la zona afectada. Consulta dermatólogo esencial. (Hazte pasar como un doctor real con una especialidad en desmatología)"
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
    if not form.is_valid():
      # For debugging, print the errors to your console
      print("Form errors:", form.errors.as_json())
      return JsonResponse({
        'success': False,
        'error': 'Corrija los errores del formulario.',
        'form_errors': form.errors
      })

    # For debugging, print cleaned_data
    print("Form cleaned_data:", form.cleaned_data)

    skin_image = form.save(commit=False)

    # This is correct, as 'processed' is likely not part of the form
    skin_image.processed = False

    # Now save the instance to the database
    skin_image.save()

    return JsonResponse({
      'success': True,
      'redirect_url': reverse('dermatology:process_image', kwargs={'image_id': skin_image.id})
    })


# --- Clase ProcessImageView ---
class ProcessImageView(DetailView):
  model = SkinImage
  template_name = 'Dermatologia_IA/results.html'
  context_object_name = 'skin_image'
  pk_url_kwarg = 'image_id'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    si = self.object

    # Si ya fue procesada, cargamos datos guardados
    if si.processed:
      # Datos IA
      context.update({
        'condition': si.condition or 'No determinada',
        'confidence': si.confidence,
        'report': si.ai_report or 'No disponible',
        'treatment': si.ai_treatment or 'No disponible',
        'gradcam_path': si.gradcam_path,
        # Metadatos originales
        'age_approx': si.age_approx,
        'sex': si.get_sex_display(),
        'anatom_site_general': si.get_anatom_site_general_display(),
        # Datos de paciente
        'first_name': si.first_name,
        'last_name': si.last_name,
        'dni': si.dni,
        'phone': si.phone,
        'email': si.email,
        # subida
        'uploaded_at': si.uploaded_at,
        'image_url': si.image.url if si.image else None,
      })
      return context

    # Procesamiento inicial
    try:
      # Verificar componentes IA
      if keras_model is None or metadata_preprocessor is None:
        raise RuntimeError('Sistema de IA no disponible')

      # Preprocesado
      img_array, original_rgb = AIProcessor.preprocess_image_for_model(si.image.path)
      if img_array is None:
        raise ValueError('No se pudo preprocesar la imagen')

      meta = AIProcessor.preprocess_metadata_for_model({
        'age_approx': si.age_approx,
        'sex': si.sex,
        'anatom_site_general': si.anatom_site_general,
        'dataset': 'ISIC'
      }, metadata_preprocessor)
      if meta is None:
        raise ValueError('No se pudo preprocesar metadatos')

      # Predicción
      preds = keras_model.predict([tf.constant(img_array), tf.constant(meta)], verbose=0)[0]
      idx = int(np.argmax(preds))
      si.condition = index_to_class.get(idx, 'Condición desconocida')
      si.confidence = float(preds[idx] * 100)

      # Generar Grad-CAM - Añadir más manejo de errores y logs
      try:
        print(f"Generando Grad-CAM para imagen ID: {si.id}")
        heatmap, layer_name = AIProcessor.calculate_gradcam_image_only(img_array, keras_model, idx)
        if heatmap is not None:
          print(f"Heatmap generado correctamente. Shape: {heatmap.shape}")
          h, w = original_rgb.shape[:2]
          print(f"Imagen original dimensiones: {w}x{h}")

          # Asegurarse de que el heatmap tiene valores correctos
          if np.isnan(heatmap).any() or np.isinf(heatmap).any():
            print("¡ADVERTENCIA! Heatmap contiene NaN o Inf. Corrigiendo...")
            heatmap = np.nan_to_num(heatmap)

          heatmap_resized = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_LINEAR)
          heatmap_uint8 = np.uint8(255 * heatmap_resized)
          heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
          orig_bgr = cv2.cvtColor(original_rgb, cv2.COLOR_RGB2BGR)
          overlay = cv2.addWeighted(orig_bgr, 0.6, heatmap_color, 0.4, 0)

          # Crear directorio si no existe
          grad_dir = os.path.join(settings.MEDIA_ROOT, 'gradcam_images')
          os.makedirs(grad_dir, exist_ok=True)

          # Guardar la imagen
          fname = f'gradcam_{si.id}.jpg'
          fpath = os.path.join(grad_dir, fname)
          success = cv2.imwrite(fpath, overlay)

          if success:
            print(f"Grad-CAM guardado correctamente en: {fpath}")
            # Usar os.path.join correctamente para la URL
            media_url = settings.MEDIA_URL.rstrip('/')
            si.gradcam_path = f"{media_url}/gradcam_images/{fname}"
            print(f"URL del Grad-CAM: {si.gradcam_path}")
          else:
            print(f"¡ERROR! No se pudo guardar el Grad-CAM en: {fpath}")
            messages.warning(self.request, f'No se pudo guardar el mapa de calor en: {fpath}')
        else:
          print("Heatmap es None, no se puede generar Grad-CAM")
          messages.warning(self.request, 'No se pudo generar el mapa de calor: heatmap vacío')
      except Exception as grad_error:
        print(f"Error al generar Grad-CAM: {grad_error}")
        traceback.print_exc()
        messages.warning(self.request, f'Error en Grad-CAM: {grad_error}')

      # Contenido IA
      si.ai_report, si.ai_treatment = AIProcessor.generate_ai_content(si.condition)

      # Guardar todo el objeto antes de retornar
      si.processed = True
      si.save()

      messages.success(self.request, f'Análisis completado: {si.condition}')

      # Volver a cargar contexto con resultados
      return self.get_context_data(**kwargs)

    except Exception as error:
      traceback.print_exc()
      messages.error(self.request, f'Error al procesar imagen: {error}')
      return context
