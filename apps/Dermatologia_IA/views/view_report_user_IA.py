"""
Vistas para la gestión de pacientes y sus análisis dermatológicos.
Incluye las vistas para listar, crear, actualizar pacientes y gestionar sus análisis.
"""
import logging
import os
import traceback

import cv2
import google.generativeai as genai
import numpy as np
import tensorflow as tf
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import get_custom_objects

from apps.Dermatologia_IA.forms.form_patient import PatientForm
from apps.Dermatologia_IA.forms.form_report_user_IA import SkinImageForm
from apps.Dermatologia_IA.models import SkinImage, Patient
from apps.auth.views.view_auth import CustomLoginRequiredMixin

logger = logging.getLogger(__name__)


# --- Definición de CustomF1Score con Registro para Serialización ---

@tf.keras.utils.register_keras_serializable()
class CustomF1Score(tf.keras.metrics.Metric):
  def __init__(self, num_classes, name='f1_score', **kwargs):
    super(CustomF1Score, self).__init__(name=name, **kwargs)
    self.num_classes = num_classes
    self.true_positives = self.add_weight(
      name='tp', shape=(num_classes,), initializer='zeros'
    )
    self.false_positives = self.add_weight(
      name='fp', shape=(num_classes,), initializer='zeros'
    )
    self.false_negatives = self.add_weight(
      name='fn', shape=(num_classes,), initializer='zeros'
    )

  def update_state(self, y_true, y_pred, sample_weight=None):
    y_true = tf.cast(y_true, tf.int32)
    y_pred = tf.cast(tf.argmax(y_pred, axis=-1), tf.int32)
    y_true_one_hot = tf.one_hot(y_true, depth=self.num_classes)
    y_pred_one_hot = tf.one_hot(y_pred, depth=self.num_classes)

    tp = tf.reduce_sum(y_true_one_hot * y_pred_one_hot, axis=0)
    fp = tf.reduce_sum((1 - y_true_one_hot) * y_pred_one_hot, axis=0)
    fn = tf.reduce_sum(y_true_one_hot * (1 - y_pred_one_hot), axis=0)

    self.true_positives.assign_add(tp)
    self.false_positives.assign_add(fp)
    self.false_negatives.assign_add(fn)

  def result(self):
    precision = self.true_positives / (self.true_positives + self.false_positives + tf.keras.backend.epsilon())
    recall = self.true_positives / (self.true_positives + self.false_negatives + tf.keras.backend.epsilon())
    f1 = 2 * (precision * recall) / (precision + recall + tf.keras.backend.epsilon())
    return tf.reduce_mean(f1)

  def reset_states(self):
    self.true_positives.assign(tf.zeros(self.num_classes))
    self.false_positives.assign(tf.zeros(self.num_classes))
    self.false_negatives.assign(tf.zeros(self.num_classes))

  def get_config(self):
    config = super(CustomF1Score, self).get_config()
    config.update({'num_classes': self.num_classes})
    return config

  @classmethod
  def from_config(cls, config):
    return cls(**config)


# Registrar la métrica personalizada (redundante con el decorador, pero por seguridad)
get_custom_objects().update({'CustomF1Score': CustomF1Score})

# --- Configuración de Rutas y Carga del Modelo ---

RESULTS_DIR = os.path.join(settings.BASE_DIR, 'Entrenamiento_IA', 'RESULTADOS_DEL_MODELO_ENTRENADO')
MODEL_FILENAME = 'Modelo_IA_Entrenada.keras'
MODEL_PATH = os.path.join(RESULTS_DIR, MODEL_FILENAME)

# Lista de clases (25 clases como en tu entrenamiento)
CLASS_NAMES = [
  "MEL", "NV", "BCC", "AK", "BKL", "DF", "VASC", "SCC", "UNK",
  "ACN", "ROS", "DER", "ECZ", "PSO", "IMP", "CEL", "RIN",
  "HER", "LUP", "HIV", "WAR", "SCA", "VAS", "CPX", "SHG"
]
index_to_class = {i: name for i, name in enumerate(CLASS_NAMES)}

# Diccionario de nombres completos de enfermedades
disease_names = {
  "MEL": "Melanoma",
  "NV": "Nevus",
  "BCC": "Carcinoma de células basales",
  "AK": "Queratosis actínica",
  "BKL": "Queratosis benigna",
  "DF": "Dermatofibroma",
  "VASC": "Lesiones vasculares",
  "SCC": "Carcinoma de células escamosas",
  "UNK": "Desconocido",
  "ACN": "Acné",
  "ROS": "Rosácea",
  "DER": "Dermatitis",
  "ECZ": "Eczema",
  "PSO": "Psoriasis",
  "IMP": "Impétigo",
  "CEL": "Celulitis",
  "RIN": "Tiña",
  "HER": "Herpes",
  "LUP": "Lupus",
  "HIV": "VIH-relacionado",
  "WAR": "Verrugas",
  "SCA": "Sarna",
  "VAS": "Vasculitis",
  "CPX": "Varicela",
  "SHG": "Herpes zóster"
}

# --- Carga del Modelo Keras ---
try:
  if os.path.exists(MODEL_PATH):
    keras_model = load_model(MODEL_PATH, custom_objects={'CustomF1Score': CustomF1Score})
    print(f'Se encontró el modelo')
    keras_model.summary()  # Log the model summary to inspect layers
    # Log the input structure
    logger.debug(f"Model inputs: {keras_model.inputs}")
  else:
    print(f"Advertencia: No se encontró el modelo en {MODEL_PATH}")
    keras_model = None
except Exception as e:
  print(f"Error al cargar el modelo desde {MODEL_PATH}: {e}")
  keras_model = None

# --- Configuración de Gemini AI ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
gemini_model = None
if GEMINI_API_KEY:
  genai.configure(api_key=GEMINI_API_KEY)
  gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')


# ------------------ VISTAS DE PACIENTE ------------------

class PatientListView(CustomLoginRequiredMixin, ListView):
  """Vista para listar pacientes con opciones de búsqueda y paginación."""
  model = Patient
  template_name = 'Dermatologia_IA/patient_list.html'
  context_object_name = 'patients'
  paginate_by = 20

  def get_queryset(self):
    """Filtra los pacientes por DNI si se proporciona en la búsqueda."""
    queryset = super().get_queryset()
    dni = self.request.GET.get('dni', '').strip()
    if dni:
      queryset = queryset.filter(dni__icontains=dni)
    return queryset

  def get_context_data(self, **kwargs):
    """Prepara el contexto con textos y configuración de la interfaz."""
    context = super().get_context_data(**kwargs)
    context.update({
      'page_title': 'Gestión de Pacientes',
      'page_subtitle': 'Lista de pacientes registrados en el sistema',
      'app_name': 'DermaIA',
      'current_section': 'patients',
      'texts': {
        'search_placeholder': 'Buscar por número de cédula',
        'add_button': 'Registrar Nuevo Paciente',
        'no_results': 'No se encontraron pacientes registrados.',
        'table_headers': {
          'name': 'Nombre',
          'lastname': 'Apellido',
          'dni': 'Cédula',
          'consultations': 'Consultas',
          'actions': 'Acciones'
        }
      },
      'actions': {
        'search': {
          'button_text': 'Buscar',
          'button_class': 'btn-primary'
        },
        'add': {
          'button_text': 'Agregar Paciente',
          'button_class': 'btn-success',
          'url_name': 'dermatology:patient-create'
        },
        'edit': {
          'button_text': 'Editar',
          'button_class': 'btn-warning btn-sm'
        }
      },
      'pagination': {
        'previous': 'Anterior',
        'next': 'Siguiente',
        'page_text': 'Página {current} de {total}'
      }
    })
    return context


class PatientFormMixin:
  """Mixin con funcionalidad común para las vistas de formulario de paciente."""

  def get_base_context(self, form_title):
    """Retorna el contexto base para los formularios de paciente."""
    return {
      'page_title': form_title,
      'app_name': 'DermaIA',
      'current_section': 'patients',
      'field_labels': {
        'first_name': 'Nombres',
        'last_name': 'Apellidos',
        'dni': 'Cédula',
        'phone': 'Teléfono',
        'email': 'Correo Electrónico',
        'age_approx': 'Edad',
        'sex': 'Sexo'
      },
      'buttons': {
        'submit': {
          'text': 'Guardar',
          'class': 'btn-primary btn-lg'
        },
        'cancel': {
          'text': 'Cancelar',
          'class': 'btn-secondary',
          'url': reverse_lazy('dermatology:patient-list')
        }
      }
    }


class PatientCreateView(CustomLoginRequiredMixin, PatientFormMixin, CreateView):
  """Vista para crear nuevos pacientes."""
  model = Patient
  form_class = PatientForm
  template_name = 'Dermatologia_IA/patient_form.html'
  success_url = reverse_lazy('dermatology:patient-list')

  def get_context_data(self, **kwargs):
    """Añade el contexto específico para la creación de pacientes."""
    context = super().get_context_data(**kwargs)
    form_context = self.get_base_context('Registro de Nuevo Paciente')
    form_context.update({
      'subtitle': 'Complete el formulario para registrar un nuevo paciente',
      'buttons': {
        'submit': {
          'text': 'Crear Paciente',
          'class': 'btn-success btn-lg'
        },
        'cancel': {
          'text': 'Cancelar',
          'class': 'btn-secondary',
          'url': reverse_lazy('dermatology:patient-list')
        }
      }
    })
    context.update(form_context)
    return context

  def form_valid(self, form):
    """Maneja el éxito en la creación del paciente."""
    response = super().form_valid(form)
    messages.success(self.request, 'Paciente registrado exitosamente.')
    return response


class PatientUpdateView(CustomLoginRequiredMixin, PatientFormMixin, UpdateView):
  """Vista para actualizar la información de pacientes existentes."""
  model = Patient
  form_class = PatientForm
  template_name = 'Dermatologia_IA/patient_form.html'
  success_url = reverse_lazy('dermatology:patient-list')

  def get_context_data(self, **kwargs):
    """Añade el contexto específico para la actualización de pacientes."""
    context = super().get_context_data(**kwargs)
    patient = self.get_object()
    form_context = self.get_base_context('Actualización de Paciente')
    form_context.update({
      'subtitle': f'Editando información de {patient.get_full_name()}',
      'buttons': {
        'submit': {
          'text': 'Guardar Cambios',
          'class': 'btn-primary btn-lg'
        },
        'cancel': {
          'text': 'Cancelar',
          'class': 'btn-secondary',
          'url': reverse_lazy('dermatology:patient-list')
        }
      }
    })
    context.update(form_context)
    return context

  def form_valid(self, form):
    """Maneja el éxito en la actualización del paciente."""
    response = super().form_valid(form)
    messages.success(self.request, 'Información del paciente actualizada exitosamente.')
    return response


# ------------------ VISTA DE SUBIDA / IMAGE UPLOAD ------------------

# class UploadImageView(CustomLoginRequiredMixin, View):
#   """Vista para subir imágenes y asociarlas con pacientes."""
#   template_name = 'Dermatologia_IA/upload.html'
#
#   def get(self, request):
#     """Maneja la solicitud GET mostrando el formulario de carga."""
#     context = {
#       'page_title': 'Nuevo Análisis Dermatológico',
#       'subtitle': 'Suba una imagen para análisis con IA',
#       'form': SkinImageForm(),
#       'upload_section': {
#         'title': 'Análisis Dermatológico con IA',
#         'patient_search': {
#           'label': 'Buscar paciente por cédula',
#           'placeholder': 'Ingrese el número de cédula',
#           'button_text': 'Buscar',
#           'no_results': 'No se encontró ningún paciente con esa cédula'
#         },
#         'new_patient': {
#           'button_text': 'Registrar Nuevo Paciente',
#           'title': 'Datos del Nuevo Paciente'
#         },
#         'image_upload': {
#           'title': 'Subir Imagen',
#           'instructions': 'Arrastra una imagen aquí o haz clic para seleccionar',
#           'formats': 'Formatos aceptados: JPG, PNG, JPEG',
#           'preview_alt': 'Vista previa de la imagen'
#         },
#         'location': {
#           'label': 'Localización Anatómica',
#           'placeholder': 'Seleccione la zona del cuerpo'
#         }
#       },
#       'buttons': {
#         'submit': {
#           'text': 'Analizar Imagen',
#           'class': 'btn-primary btn-lg'
#         }
#       },
#       'loading': {
#         'message': 'Analizando su imagen...',
#         'submessage': 'Este proceso puede tardar unos segundos'
#       }
#     }
#
#     # Si hay una búsqueda por DNI, filtrar pacientes
#     dni_query = request.GET.get('dni', '').strip()
#     if dni_query:
#       pacientes = Patient.objects.filter(dni__icontains=dni_query)
#       context['patients'] = pacientes
#       if not pacientes.exists():
#         messages.info(request, context['upload_section']['patient_search']['no_results'])
#
#     return render(request, self.template_name, context)
#
#   def post(self, request):
#     """Maneja la solicitud POST procesando la imagen y datos del paciente."""
#     try:
#       # Validar si es paciente existente o nuevo
#       patient_id = request.POST.get('patient')
#
#       if patient_id:
#         patient = get_object_or_404(Patient, id=patient_id)
#       else:
#         # Crear nuevo paciente
#         patient_form = PatientForm(request.POST)
#         if not patient_form.is_valid():
#           return JsonResponse({
#             'success': False,
#             'errors': patient_form.errors
#           })
#         patient = patient_form.save()
#
#       # Procesar la imagen
#       form = SkinImageForm(request.POST, request.FILES)
#       if not form.is_valid():
#         return JsonResponse({
#           'success': False,
#           'errors': form.errors
#         })
#
#       skin_image = form.save(commit=False)
#       skin_image.patient = patient
#       skin_image.processed = False
#       skin_image.save()
#
#       return JsonResponse({
#         'success': True,
#         'redirect_url': reverse('dermatology:process_image', kwargs={'image_id': skin_image.id})
#       })
#
#     except Exception as e:
#       logger.error(f"Error en carga de imagen: {str(e)}")
#       return JsonResponse({
#         'success': False,
#         'errors': {'general': 'Error al procesar la solicitud.'}
#       })

class UploadImageView(CustomLoginRequiredMixin, View):
  """Vista para subir imágenes y asociarlas con pacientes."""
  template_name = 'Dermatologia_IA/upload.html'

  def get(self, request):
    """Maneja la solicitud GET mostrando el formulario de carga."""
    # Load up to 5 patients initially
    initial_patients = Patient.objects.all().order_by('-id')[:5]
    # initial_patients = Patient.objects.all()[:5]
    context = {
      'page_title': 'Nuevo Análisis Dermatológico',
      'subtitle': 'Suba una imagen para análisis con IA',
      'form': SkinImageForm(),
      'upload_section': {
        'title': 'Análisis Dermatológico con IA',
        'patient_search': {
          'label': 'Seleccionar paciente por cédula',
          'placeholder': 'Busque por cédula',
          'no_results': 'No se encontró ningún paciente con esa cédula'
        },
        'new_patient': {
          'button_text': 'Registrar Nuevo Paciente',
          'title': 'Datos del Nuevo Paciente'
        },
        'image_upload': {
          'title': 'Subir Imagen',
          'instructions': 'Arrastra una imagen aquí o haz clic para seleccionar',
          'formats': 'Formatos aceptados: JPG, PNG, JPEG',
          'preview_alt': 'Vista previa de la imagen'
        },
        'location': {
          'label': 'Localización Anatómica',
          'placeholder': 'Seleccione la zona del cuerpo'
        }
      },
      'buttons': {
        'submit': {
          'text': 'Analizar Imagen',
          'class': 'btn-primary btn-lg'
        }
      },
      'loading': {
        'message': 'Analizando su imagen...',
        'submessage': 'Este proceso puede tardar unos segundos'
      },
      'patients': initial_patients  # Pass initial patients
    }
    return render(request, self.template_name, context)

  def post(self, request):
    """Maneja la solicitud POST procesando la imagen y datos del paciente."""
    try:
      patient_id = request.POST.get('patient')

      if patient_id:
        patient = get_object_or_404(Patient, id=patient_id)
      else:
        patient_form = PatientForm(request.POST)
        if not patient_form.is_valid():
          return JsonResponse({
            'success': False,
            'errors': patient_form.errors
          })
        patient = patient_form.save()

      form = SkinImageForm(request.POST, request.FILES)
      if not form.is_valid():
        return JsonResponse({
          'success': False,
          'errors': form.errors
        })

      skin_image = form.save(commit=False)
      skin_image.patient = patient
      skin_image.processed = False
      skin_image.save()

      return JsonResponse({
        'success': True,
        'redirect_url': reverse('dermatology:process_image', kwargs={'image_id': skin_image.id})
      })

    except Exception as e:
      logger.error(f"Error en carga de imagen: {str(e)}")
      return JsonResponse({
        'success': False,
        'errors': {'general': 'Error al procesar la solicitud.'}
      })


class SearchPatientsView(CustomLoginRequiredMixin, View):
  """Vista para buscar pacientes dinámicamente por DNI."""

  def get(self, request):
    dni_query = request.GET.get('dni', '').strip()
    if not dni_query:
      patients = Patient.objects.all().order_by('-id')[:5]
      # patients = Patient.objects.all()[:5]
    else:
      patients = Patient.objects.filter(dni__istartswith=dni_query)[:5]

    patients_data = [
      {
        'id': patient.id,
        'first_name': patient.first_name,
        'last_name': patient.last_name,
        'dni': patient.dni,
        'phone': patient.phone or '',
        'email': patient.email or '',
        'age_approx': patient.age_approx,
        'sex': patient.sex
      }
      for patient in patients
    ]
    return JsonResponse({'patients': patients_data})


# ------------------ VISTA DE PROCESO DE IMAGEN ------------------

class ResultsViewMixin:
  """Mixin para compartir configuración común entre vistas que usan results.html"""
  template_name = 'Dermatologia_IA/results.html'
  context_object_name = 'skin_image'

  def get_base_context(self):
    """Retorna el contexto base para el template results.html"""
    return {
      'page_title': 'Análisis Dermatológico',
      'sections': {
        'patient_info': {
          'title': 'Información del Paciente',
          'fields': {
            'name': 'Nombre completo',
            'dni': 'Cédula',
            'age': 'Edad',
            'sex': 'Sexo',
            'phone': 'Teléfono',
            'email': 'Correo'
          }
        },
        'analysis': {
          'title': 'Resultados del Análisis',
          'fields': {
            'condition': 'Condición Detectada',
            'confidence': 'Nivel de Confianza',
            'location': 'Localización',
            'date': 'Fecha de Análisis'
          }
        },
        'ai_info': {
          'report_title': 'Reporte de IA',
          'treatment_title': 'Tratamiento Sugerido'
        },
        'images': {
          'title': 'Imágenes',
          'original': 'Imagen Original',
          'heatmap': 'Mapa de Calor (Grad-CAM)'
        }
      },
      'buttons': {
        'download': {
          'text': 'Descargar PDF',
          'class': 'btn-primary',
          'icon': 'bi-file-pdf'
        },
        'email': {
          'text': 'Enviar por Email',
          'class': 'btn-info',
          'icon': 'bi-envelope'
        },
        'new': {
          'text': 'Nueva Consulta',
          'class': 'btn-secondary',
          'icon': 'bi-arrow-left'
        }
      },
    }


class ProcessImageView(CustomLoginRequiredMixin, ResultsViewMixin, DetailView):
  """Vista para procesar y mostrar resultados del análisis de imagen."""
  model = SkinImage
  pk_url_kwarg = 'image_id'

  def get_context_data(self, **kwargs):
    """Añade el contexto específico para la vista de procesamiento."""
    context = super().get_context_data(**kwargs)
    context.update(self.get_base_context())

    # Mostrar botones solo en vista de procesamiento
    context['show_actions'] = True

    si = self.object
    if not si.processed:
      try:
        if keras_model is None:
          raise RuntimeError('Sistema de IA no disponible')

        img_array, original_rgb = AIProcessor.preprocess_image_for_model(si.image.path)
        if img_array is None:
          raise ValueError('No se pudo preprocesar la imagen')

        # Pasamos solo la imagen al modelo
        preds = keras_model.predict(tf.constant(img_array), verbose=0)[0]
        idx = int(np.argmax(preds))
        predicted_class = index_to_class.get(idx, 'Condición desconocida')
        disease_name = disease_names.get(predicted_class, 'Desconocido')
        si.condition = disease_name  # Usamos el nombre completo de la enfermedad
        si.confidence = float(preds[idx] * 100)

        try:
          heatmap, layer_name = AIProcessor.calculate_gradcam_image_only(img_array, keras_model, idx)
          if heatmap is not None:
            h, w = original_rgb.shape[:2]
            if np.isnan(heatmap).any() or np.isinf(heatmap).any():
              heatmap = np.nan_to_num(heatmap)
            heatmap_resized = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_LINEAR)
            heatmap_uint8 = np.uint8(255 * heatmap_resized)
            heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
            orig_bgr = cv2.cvtColor(original_rgb, cv2.COLOR_RGB2BGR)
            overlay = cv2.addWeighted(orig_bgr, 0.6, heatmap_color, 0.4, 0)

            grad_dir = os.path.join(settings.MEDIA_ROOT, 'gradcam_images')
            os.makedirs(grad_dir, exist_ok=True)
            fname = f'gradcam_{si.id}.jpg'
            fpath = os.path.join(grad_dir, fname)
            success = cv2.imwrite(fpath, overlay)
            if success:
              # Construct the relative path for the media URL
              relative_path = os.path.join('gradcam_images', fname)
              si.gradcam_path = relative_path  # Store the relative path
              logger.debug(f"Grad-CAM image saved at: {fpath}, gradcam_path set to: {relative_path}")
            else:
              messages.warning(self.request, f'No se pudo guardar el mapa de calor en: {fpath}')
              logger.error(f"Failed to save Grad-CAM image at: {fpath}")
          else:
            messages.warning(self.request, 'No se pudo generar el mapa de calor: heatmap vacío')
            logger.warning("Heatmap is None after Grad-CAM computation")
        except Exception as grad_error:
          messages.warning(self.request, f'Error en Grad-CAM: {grad_error}')
          logger.error(f"Grad-CAM error: {str(grad_error)}")

        si.ai_report, si.ai_treatment = AIProcessor.generate_ai_content(si.condition)

        si.processed = True
        si.save()
        logger.debug(f"SkinImage {si.id} processed: {si.processed}, gradcam_path: {si.gradcam_path}")
        messages.success(self.request, f'Análisis completado: {si.condition}')
        logger.debug(f"Message set: Análisis completado: {si.condition}")

        return self.get_context_data(**kwargs)  # Return updated context

      except Exception as error:
        messages.error(self.request, f'Error al procesar imagen: {error}')
        context['error'] = str(error)
        logger.error(f"Processing error: {str(error)}")

    return context


# --- Clase AIProcessor ---

class AIProcessor:
  @staticmethod
  def preprocess_image_for_model(image_path):
    try:
      img = cv2.imread(image_path)
      if img is None:
        raise ValueError(f"No se pudo cargar la imagen desde: {image_path}")
      img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
      img_resized = cv2.resize(img_rgb, (224, 224))
      img_preprocessed = preprocess_input(img_resized)  # Usando MobileNetV2 preprocess_input
      img_array = np.expand_dims(img_preprocessed, axis=0)
      return img_array, img_rgb
    except Exception as e:
      traceback.print_exc()
      return None, None

  @staticmethod
  def calculate_gradcam_image_only(img_array, model, pred_index):
    try:
      # Find the last convolutional layer directly
      last_conv_layer = None
      last_conv_layer_name = None
      for layer in reversed(model.layers):
        if isinstance(layer, (tf.keras.layers.Conv2D, tf.keras.layers.DepthwiseConv2D)):
          last_conv_layer = layer
          last_conv_layer_name = layer.name
          break
      if not last_conv_layer:
        raise ValueError("No se encontró ninguna capa convolucional en el modelo")

      # Log the input structure for debugging
      logger.debug(f"Model inputs for Grad-CAM: {model.inputs}")

      # Create a model that maps the input image to the activations of the last conv layer
      # and the output predictions
      grad_model = tf.keras.Model(
        inputs=model.inputs,
        outputs=[last_conv_layer.output, model.output]
      )

      # Since model.inputs is a list (e.g., [<InputLayer>]), wrap img_array in a list
      input_tensor = [img_array] if isinstance(model.inputs, list) else img_array

      # Compute the gradient of the top predicted class for the last conv layer
      with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(input_tensor, training=False)
        loss = predictions[:, pred_index]

      # Get the gradients of the loss with respect to the conv layer outputs
      grads = tape.gradient(loss, conv_outputs)
      if grads is None:
        raise ValueError("No se pudieron calcular los gradientes")

      # Log shapes for debugging
      logger.debug(f"conv_outputs shape: {conv_outputs.shape}")
      logger.debug(f"grads shape: {grads.shape}")

      # Compute the global average pooled gradients
      pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))  # Shape: [1280]
      logger.debug(f"pooled_grads shape: {pooled_grads.shape}")

      # Broadcast pooled_grads to match conv_outputs shape [7, 7, 1280]
      conv_outputs_shape = tf.shape(conv_outputs)[1:3]  # Get [7, 7]
      pooled_grads_broadcast = tf.tile(
        pooled_grads[tf.newaxis, tf.newaxis, :],
        [conv_outputs_shape[0], conv_outputs_shape[1], 1]
      )  # Shape: [7, 7, 1280]
      logger.debug(f"pooled_grads_broadcast shape: {pooled_grads_broadcast.shape}")

      # Multiply each channel in the feature map array by its gradient importance
      conv_outputs = conv_outputs[0]  # Remove batch dimension
      heatmap = tf.reduce_mean(conv_outputs * pooled_grads_broadcast, axis=-1)

      # Normalize the heatmap
      heatmap = tf.maximum(heatmap, 0)  # ReLU
      max_val = tf.reduce_max(heatmap)
      if max_val == 0:
        return None, last_conv_layer_name
      heatmap = heatmap / max_val  # Normalize between 0 and 1

      heatmap_np = heatmap.numpy()
      return heatmap_np, last_conv_layer_name

    except Exception as e:
      traceback.print_exc()
      logger.error(f"Error en Grad-CAM: {str(e)}")
      return None, None

  @staticmethod
  def generate_ai_content(condition):
    default_report = f"Descripción no disponible para {condition}. Consulte a un dermatólogo."
    default_treatment = f"Tratamiento no disponible para {condition}. Busque atención médica."
    if not gemini_model:
      return default_report, default_treatment
    try:
      report_prompt = f"Describe brevemente (máx. 500 caracteres) la condición {condition}: qué es, síntomas, causas."
      treatment_prompt = f"Recomendaciones breves (máx. 500 caracteres) para la condición {condition}: tratamientos generales, cuidados."
      config = genai.types.GenerationConfig(max_output_tokens=150, temperature=0.7)
      report_response = gemini_model.generate_content(report_prompt, generation_config=config)
      treatment_response = gemini_model.generate_content(treatment_prompt, generation_config=config)
      ai_report = report_response.text.strip() if hasattr(report_response, 'text') else default_report
      ai_treatment = treatment_response.text.strip() if hasattr(treatment_response, 'text') else default_treatment
      return ai_report[:500], ai_treatment[:500]
    except Exception:
      return default_report, default_treatment


class ReportListView(CustomLoginRequiredMixin, ListView):
  model = SkinImage
  template_name = 'Dermatologia_IA/report_list.html'
  context_object_name = 'reports'

  def get_queryset(self):
    return SkinImage.objects.filter(processed=True)


class ReportDetailView(CustomLoginRequiredMixin, ResultsViewMixin, DetailView):
  """Vista para mostrar detalles de un reporte existente."""
  model = SkinImage
  pk_url_kwarg = 'image_id'

  def get_context_data(self, **kwargs):
    """Añade el contexto específico para la vista de detalles."""
    context = super().get_context_data(**kwargs)
    base_context = self.get_base_context()
    # En vista de detalles, no mostrar botones de acción
    base_context['show_actions'] = False
    context.update(base_context)
    return context
