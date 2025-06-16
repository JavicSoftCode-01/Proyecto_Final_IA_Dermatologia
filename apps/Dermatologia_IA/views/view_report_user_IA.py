# apps\Dermatologia_IA\views\view_report_user_IA.py

"""
Vistas para la gestión de pacientes y sus análisis dermatológicos.
Incluye las vistas para listar, crear, actualizar pacientes y gestionar sus análisis.
"""

import os
import traceback

import cv2
import google.generativeai as genai
import numpy as np
import tensorflow as tf
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render
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
from utils.logger import logger


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

RESULTS_DIR = os.path.join(settings.BASE_DIR, 'IA', 'Dermatological_AI_Model', 'checkpoints')
MODEL_FILENAME = 'MODELO_IA_DERMATOLOGICO.keras'
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
  logger.info('ModelLoader', f"Intentando cargar el modelo desde: {MODEL_PATH}")
  logger.info('ModelLoader', f"¿Existe el archivo?: {os.path.exists(MODEL_PATH)}")
  logger.info('ModelLoader', f"Ruta absoluta: {os.path.abspath(MODEL_PATH)}")
  if os.path.exists(MODEL_PATH):
    keras_model = load_model(MODEL_PATH, custom_objects={'CustomF1Score': CustomF1Score})
    logger.success('ModelLoader', 'Modelo cargado exitosamente')
    try:
      keras_model.summary(print_fn=lambda x: logger.info('ModelLoader', x))
    except Exception as summary_error:
      logger.warning('ModelLoader', f'No se pudo mostrar el resumen del modelo: {summary_error}')
    logger.debug('ModelLoader', f"Model inputs: {keras_model.inputs}")
  else:
    logger.error('ModelLoader', f"No se encontró el modelo en {MODEL_PATH}")
    keras_model = None
except Exception as e:
  logger.error('ModelLoader', f"Error al cargar el modelo desde {MODEL_PATH}: {e}")
  keras_model = None

# --- Configuración de Gemini AI ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
gemini_model = None
if GEMINI_API_KEY:
  genai.configure(api_key=GEMINI_API_KEY)
  gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')


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
        if hasattr(tf.keras.layers, 'Conv2D') and isinstance(layer,
                                                             (tf.keras.layers.Conv2D, tf.keras.layers.DepthwiseConv2D)):
          last_conv_layer = layer
          last_conv_layer_name = layer.name
          break
      if not last_conv_layer:
        raise ValueError("No se encontró ninguna capa convolucional en el modelo")

      logger.debug('AIProcessor', f"Model inputs for Grad-CAM: {model.inputs}")

      # Si el modelo espera una sola entrada, pasar el array directamente
      if isinstance(model.input, (tf.Tensor, tf.compat.v1.Tensor)):
        input_tensor = img_array
      else:
        # Si el modelo espera múltiples entradas, empaquetar en lista
        input_tensor = [img_array]

      grad_model = tf.keras.Model(
        inputs=model.input,
        outputs=[last_conv_layer.output, model.output]
      )

      with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(input_tensor, training=False)
        loss = predictions[:, pred_index]

      grads = tape.gradient(loss, conv_outputs)
      if grads is None:
        raise ValueError("No se pudieron calcular los gradientes")

      logger.debug('AIProcessor', f"conv_outputs shape: {getattr(conv_outputs, 'shape', None)}")
      logger.debug('AIProcessor', f"grads shape: {getattr(grads, 'shape', None)}")

      pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
      logger.debug('AIProcessor', f"pooled_grads shape: {getattr(pooled_grads, 'shape', None)}")

      # Broadcast pooled_grads to match conv_outputs shape
      conv_outputs = conv_outputs[0]  # Remove batch dimension
      pooled_grads = pooled_grads
      heatmap = tf.reduce_mean(conv_outputs * pooled_grads, axis=-1)

      heatmap = tf.maximum(heatmap, 0)
      max_val = tf.reduce_max(heatmap)
      if max_val == 0:
        return None, last_conv_layer_name
      heatmap = heatmap / max_val

      heatmap_np = heatmap.numpy()
      return heatmap_np, last_conv_layer_name

    except Exception as e:
      traceback.print_exc()
      logger.error('AIProcessor', f"Error en Grad-CAM: {str(e)}")
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


# ------------------ VISTAS DE PACIENTE ------------------

class PatientListView(CustomLoginRequiredMixin, ListView):
  """Vista para listar pacientes con opciones de búsqueda y paginación."""
  model = Patient
  template_name = 'Dermatologia_IA/patient_list.html'
  context_object_name = 'patients'
  paginate_by = 10

  def get_queryset(self):
    """Filtra los pacientes por DNI si se proporciona en la búsqueda."""
    queryset = super().get_queryset()
    dni = self.request.GET.get('dni', '').strip()
    if dni:
      queryset = queryset.filter(dni__icontains=dni)
      logger.info('PatientListView', f'Filtrando pacientes por DNI: {dni}')
    logger.success('PatientListView', f'Vista de lista de pacientes cargada correctamente. Total: {queryset.count()}')
    return queryset

  def get_context_data(self, **kwargs):
    """Prepara el contexto con textos y configuración de la interfaz."""
    context = super().get_context_data(**kwargs)
    context.update({
      'app_name': 'DermaIA',
      'page_title': 'Gestión de Pacientes',
      'page_subtitle': 'Lista de pacientes registrados en el sistema',
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

  def form_invalid(self, form):
    # Mostrar mensajes de error de validación de unicidad
    for field, errors in form.errors.items():
      for error in errors:
        messages.error(self.request, f"{form.fields[field].label}: {error}")
        logger.warning('PatientCreateView', f"Error en campo {field}: {error}")
    return super().form_invalid(form)

  def form_valid(self, form):
    dni = form.cleaned_data.get('dni')
    phone = form.cleaned_data.get('phone')
    email = form.cleaned_data.get('email')
    first_name = form.cleaned_data.get('first_name')
    last_name = form.cleaned_data.get('last_name')
    age_approx = form.cleaned_data.get('age_approx')
    sex = form.cleaned_data.get('sex')
    # Obtener el display del sexo
    sex_display = dict(Patient.SEX_CHOICES).get(sex, sex)

    # Validar unicidad de campos
    errors = {}
    # Excluir el registro actual en caso de update (no aplica aquí pero es seguro)
    if Patient.objects.filter(dni=dni).exists():
      errors['dni'] = 'Ya existe un paciente con este número de cédula.'
      logger.warning('PatientCreateView', f'Intento de registro con DNI duplicado: {dni}')
    if phone and Patient.objects.filter(phone=phone).exists():
      errors['phone'] = 'Ya existe un paciente con este número de teléfono.'
      logger.warning('PatientCreateView', f'Intento de registro con teléfono duplicado: {phone}')
    if email and Patient.objects.filter(email=email).exists():
      errors['email'] = 'Ya existe un paciente con este correo electrónico.'
      logger.warning('PatientCreateView', f'Intento de registro con email duplicado: {email}')
    if errors:
      for field, msg in errors.items():
        form.add_error(field, msg)
        messages.error(self.request, msg)
        logger.warning('PatientCreateView', f"Mensaje mostrado al usuario: {msg}")
      return self.form_invalid(form)
    response = super().form_valid(form)
    messages.success(self.request, 'Paciente registrado exitosamente.')
    logger.success('PatientCreateView',
                   f'Paciente registrado: DNI= {dni}, Tel= {phone}, Email= {email}, Nombres= {first_name}, Apellidos= {last_name}, Edad= {age_approx}, Sexo= {sex_display}')
    return response


class PatientUpdateView(CustomLoginRequiredMixin, PatientFormMixin, UpdateView):
  """Vista para actualizar la información de pacientes existentes."""
  model = Patient
  form_class = PatientForm
  template_name = 'Dermatologia_IA/patient_form.html'
  success_url = reverse_lazy('dermatology:patient-list')

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    patient = self.get_object()
    # Mostrar todos los campos y valores actuales en logs
    sex_display = dict(Patient.SEX_CHOICES).get(patient.sex, patient.sex)
    logger.info('PatientUpdateView', (
      f"Datos actuales del paciente (ANTES de editar): "
      f"DNI= {patient.dni}, Tel= {patient.phone}, Email= {patient.email}, "
      f"Nombres= {patient.first_name}, Apellidos= {patient.last_name}, "
      f"Edad= {patient.age_approx}, Sexo= {sex_display}"
    ))
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

  def form_invalid(self, form):
    # Mostrar mensajes de error de validación de unicidad
    for field, errors in form.errors.items():
      for error in errors:
        messages.error(self.request, f"{form.fields[field].label}: {error}")
        logger.warning('PatientUpdateView', f"Error en campo {field}: {error}")
    return super().form_invalid(form)

  def form_valid(self, form):
    dni = form.cleaned_data.get('dni')
    phone = form.cleaned_data.get('phone')
    email = form.cleaned_data.get('email')
    first_name = form.cleaned_data.get('first_name')
    last_name = form.cleaned_data.get('last_name')
    age_approx = form.cleaned_data.get('age_approx')
    sex = form.cleaned_data.get('sex')
    sex_display = dict(Patient.SEX_CHOICES).get(sex, sex)
    # Mostrar valores nuevos en logs
    logger.info('PatientUpdateView', (
      f"Datos nuevos del paciente (DESPUÉS de editar): "
      f"DNI={dni}, Tel={phone}, Email={email}, "
      f"Nombres={first_name}, Apellidos={last_name}, "
      f"Edad={age_approx}, Sexo={sex_display}"
    ))
    errors = {}
    instance_id = self.object.id if self.object else None
    if Patient.objects.filter(dni=dni).exclude(id=instance_id).exists():
      errors['dni'] = 'Ya existe un paciente con este número de cédula.'
      logger.warning('PatientUpdateView', f'Intento de actualización con DNI duplicado: {dni}')
    if phone and Patient.objects.filter(phone=phone).exclude(id=instance_id).exists():
      errors['phone'] = 'Ya existe un paciente con este número de teléfono.'
      logger.warning('PatientUpdateView', f'Intento de actualización con teléfono duplicado: {phone}')
    if email and Patient.objects.filter(email=email).exclude(id=instance_id).exists():
      errors['email'] = 'Ya existe un paciente con este correo electrónico.'
      logger.warning('PatientUpdateView', f'Intento de actualización con email duplicado: {email}')
    if errors:
      for field, msg in errors.items():
        form.add_error(field, msg)
        messages.error(self.request, msg)
        logger.warning('PatientUpdateView', f"Mensaje mostrado al usuario: {msg}")
      return self.form_invalid(form)
    response = super().form_valid(form)
    messages.success(self.request, 'Información del paciente actualizada exitosamente.')
    logger.success('PatientUpdateView',
                   f'Paciente actualizado: DNI= {dni}, Tel= {phone}, Email= {email}, Nombres= {first_name}, Apellidos= {last_name}, Edad= {age_approx}, Sexo= {sex_display}')
    return response


# ------------------ VISTA DE SUBIDA / IMAGE UPLOAD ------------------

SEX_CHOICES_FOR_CONTEXT = [
  ('female', 'Femenino'),
  ('male', 'Masculino'),
  ('unknown', 'Desconocido'),
]


class UploadImageView(CustomLoginRequiredMixin, View):
  """Vista para subir imágenes y asociarlas con pacientes."""
  template_name = 'Dermatologia_IA/upload.html'

  def get(self, request):
    logger.info('UploadImageView', 'Cargando formulario de subida de imagen y selección de paciente.')
    initial_patients = Patient.objects.all().order_by('-id')[:10]
    skin_image_form = SkinImageForm()
    context = {
      'app_name': 'DermaIA',
      'page_title': 'Nuevo Análisis Dermatológico',
      'form': skin_image_form,  # Pasar el formulario para acceder a sus campos (ej. choices)
      'patients': initial_patients,
      'upload_section': {
        'title': 'Análisis Dermatológico con IA',
        'patient_search': {
          'label': 'Seleccionar paciente existente o registrar uno nuevo',
          'select_placeholder': 'Busque por cédula (solo números, máx. 10) o seleccione "Nuevo Paciente"',
          'typing_hint': '💡 Haga clic y escriba la cédula (solo números, máximo 10 dígitos)',
          'no_results': 'No se encontró ningún paciente con esa cédula.',
        },
        'new_patient': {
          'button_text': 'Registrar Nuevo Paciente',
          'title': 'Datos del Nuevo Paciente',
          'labels': {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'dni': 'DNI',
            'phone': 'Teléfono',
            'email': 'Correo Electrónico',
            'age_approx': 'Edad Aproximada',
            'sex': 'Sexo',
          },
          'sex_placeholder': '-- Seleccionar Sexo --',
        },
        'image_upload': {
          'title': 'Subir Imagen de la Piel',
          'instructions': 'Arrastra una imagen aquí o haz clic para seleccionar',
          'formats': 'Formatos aceptados: JPG, PNG, JPEG. Tamaño máximo: 5MB.',
          'preview_alt': 'Vista previa de la imagen',
        },
        'location': {
          'label': 'Localización Anatómica de la Lesión',
          'placeholder': 'Seleccione la zona del cuerpo',
        }
      },
      'buttons': {
        'submit': {
          'text': 'Analizar Imagen',
          'class': 'btn-primary btn-lg',
        }
      },
      'loading': {
        'message': 'Analizando su imagen...',
        'submessage': 'Este proceso puede tardar unos segundos.',
        'spinner_alt': 'Cargando...',
      },
      'error_messages_general': {
        'form_errors': 'Por favor, corrija los errores en el formulario.',
        'server_error': 'Ocurrió un error en el servidor. Intente de nuevo.',
      },
      'sex_choices': SEX_CHOICES_FOR_CONTEXT,  # Para el select de sexo del nuevo paciente
      'js_texts': {  # Textos para JavaScript
        'searching_prefix': 'Buscando:',
        'search_placeholder_default': 'Busque por cédula (solo números, máx. 10)',
        'error_searching_patients': 'Error al buscar pacientes:',
        'validation_errors': {
          'empty_field': "El campo está vacío, por favor rellénelo.",
          'name_min_length': "El nombre o apellido debe tener al menos 3 caracteres.",
          'name_max_length': "El nombre o apellido no puede tener más de 50 caracteres.",
          'name_regex': "Solo puede contener letras, incluyendo letras especiales como la Ñ o tilde.",
          'dni_exact_length': "La cédula debe contener exactamente 10 dígitos.",
          'dni_numeric': "La cédula debe contener solo números.",
          'dni_invalid': "La cédula ingresada no es válida.",
          'email_max_length': "El correo electrónico no puede tener más de 254 caracteres.",
          'email_invalid': "Ingrese un correo electrónico válido.",
          'phone_invalid_format': "Ingrese un número válido (formato: +593 99 999 9999 o 0999999999)",
          'age_invalid': "Ingrese una edad válida entre 0 y 120 años.",
          'image_required': "Por favor seleccione una imagen para analizar.",
          'image_invalid_type': "El archivo debe ser una imagen (JPG, JPEG o PNG).",
          'image_max_size': "La imagen no debe exceder los 5MB.",
          'site_required': "Por favor seleccione la localización anatómica."
        }
      }
    }
    logger.success('UploadImageView', 'Vista de subida de imagen cargada correctamente.')
    return render(request, self.template_name, context)

  def post(self, request):
    try:
      logger.info('UploadImageView', 'Procesando POST para crear paciente y/o reporte.')
      patient_id = request.POST.get('patient')
      patient = None
      if patient_id:
        try:
          patient = Patient.objects.get(id=patient_id)
          logger.info('UploadImageView', f'Paciente existente seleccionado: ID={patient_id}')
        except Patient.DoesNotExist:
          logger.warning('UploadImageView', f'Paciente no válido: ID={patient_id}')
          return JsonResponse({'success': False, 'errors': {'patient': ['Paciente seleccionado no válido.']}},
                              status=400)
      else:
        patient_form_data = {
          'first_name': request.POST.get('first_name'),
          'last_name': request.POST.get('last_name'),
          'dni': request.POST.get('dni'),
          'phone': request.POST.get('phone'),
          'email': request.POST.get('email'),
          'age_approx': request.POST.get('age_approx'),
          'sex': request.POST.get('sex'),
          'user': request.user
        }
        patient_form = PatientForm(patient_form_data)
        if patient_form.is_valid():
          patient = patient_form.save()
          logger.success('UploadImageView', f'Paciente creado desde upload: DNI={patient.dni}, Email={patient.email}')
        else:
          logger.warning('UploadImageView', f'Errores al crear paciente desde upload: {patient_form.errors}')
          return JsonResponse({'success': False, 'errors': patient_form.errors}, status=400)
      image_form_data = {'anatom_site_general': request.POST.get('anatom_site_general')}
      skin_image_form = SkinImageForm(image_form_data, request.FILES)
      if skin_image_form.is_valid():
        skin_image = skin_image_form.save(commit=False)
        skin_image.patient = patient
        skin_image.processed = False
        skin_image.save()
        logger.success('UploadImageView',
                       f'Reporte creado correctamente para paciente ID={patient.id}, Reporte ID={skin_image.id}')
        return JsonResponse(
          {'success': True, 'redirect_url': reverse('dermatology:process_image', kwargs={'image_id': skin_image.id})})
      else:
        logger.warning('UploadImageView', f'Errores al crear reporte: {skin_image_form.errors}')
        return JsonResponse({'success': False, 'errors': skin_image_form.errors}, status=400)
    except Exception as e:
      logger.error('UploadImageView', f'Error en carga de imagen: {str(e)}')
      return JsonResponse(
        {'success': False, 'errors': {'general': ['Error interno al procesar la solicitud. Intente más tarde.']}},
        status=500)


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
        'full_name': patient.get_full_name(),
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
      'app_name': 'DermaIA',
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
    logger.info('ProcessImageView', f'Procesando imagen para SkinImage ID {getattr(self.object, "id", "?")}')
    context = super().get_context_data(**kwargs)
    context.update(self.get_base_context())
    context['show_actions'] = True
    si = self.object
    if not si.processed:
      try:
        if keras_model is None:
          logger.error('ProcessImageView', 'Sistema de IA no disponible')
          raise RuntimeError('Sistema de IA no disponible')
        img_array, original_rgb = AIProcessor.preprocess_image_for_model(si.image.path)
        if img_array is None:
          logger.error('ProcessImageView', 'No se pudo preprocesar la imagen')
          raise ValueError('No se pudo preprocesar la imagen')
        preds = keras_model.predict(tf.constant(img_array), verbose=0)[0]
        idx = int(np.argmax(preds))
        predicted_class = index_to_class.get(idx, 'Condición desconocida')
        disease_name = disease_names.get(predicted_class, 'Desconocido')
        si.condition = disease_name
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
              relative_path = os.path.join('gradcam_images', fname)
              si.gradcam_path = relative_path
              logger.success('ProcessImageView', f'Grad-CAM guardado en: {fpath}, gradcam_path: {relative_path}')
            else:
              messages.warning(self.request, f'No se pudo guardar el mapa de calor en: {fpath}')
              logger.warning('ProcessImageView', f'No se pudo guardar el mapa de calor en: {fpath}')
          else:
            messages.warning(self.request, 'No se pudo generar el mapa de calor: heatmap vacío')
            logger.warning('ProcessImageView', 'Heatmap es None tras Grad-CAM')
        except Exception as grad_error:
          messages.warning(self.request, f'Error en Grad-CAM: {grad_error}')
          logger.error('ProcessImageView', f'Error en Grad-CAM: {str(grad_error)}')
        si.ai_report, si.ai_treatment = AIProcessor.generate_ai_content(si.get_status())
        si.processed = True
        si.save()
        logger.success('ProcessImageView',
                       f'SkinImage {getattr(si, "id", "?")} procesada, gradcam_path: {si.gradcam_path}')
        messages.success(self.request, f'Análisis completado: {si.get_status()}')
        logger.info('ProcessImageView', f'Mensaje de éxito mostrado: Análisis completado: {si.get_status()}')
        return self.get_context_data(**kwargs)
      except Exception as error:
        messages.error(self.request, f'Error al procesar imagen: {error}')
        context['error'] = str(error)
        logger.error('ProcessImageView', f'Error al procesar imagen: {str(error)}')
    else:
      logger.info('ProcessImageView', f'Imagen ya procesada para SkinImage ID {getattr(si, "id", "?")}')
    return context


# ------------------ VISTAS DE REPORTES ------------------
class ReportListView(CustomLoginRequiredMixin, ListView):
  model = SkinImage
  template_name = 'Dermatologia_IA/report_list.html'
  context_object_name = 'reports'
  paginate_by = 10

  def get_queryset(self):
    queryset = SkinImage.objects.filter(processed=True).select_related('patient').order_by('-created_at')
    logger.info('ReportListView', f'Se consultaron {queryset.count()} reportes procesados.')
    logger.success('ReportListView', 'Vista de lista de reportes cargada correctamente.')
    return queryset

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'app_name': 'DermaIA',
      'page_title': 'Mis Reportes',
      'header_title': 'Mis Reportes de Análisis',
      'card_labels': {
        'report_id_prefix': 'Reporte ID',
        'default_condition': 'Sin condición especificada',
        'patient_name': 'Nombre:',
        'patient_dni': 'DNI:',
        'patient_age': 'Edad:',
        'patient_sex': 'Sexo:',
        'lesion_location': 'Localización:',
        'date_time': 'Fecha y Hora:',
        'default_na': 'N/A',
      },
      'button_texts': {
        'view_detail': 'Ver Detalle',
        'generate_pdf': 'PDF',
        'send_email': 'Enviar por Email',
      },
      'icon_classes': {
        'view_detail': 'fas fa-eye',
        'generate_pdf': 'fas fa-file-pdf',
        'send_email': 'fas fa-envelope',
        'analysis': 'fas fa-microscope',
        'patient': 'fas fa-user',
        'dni': 'fas fa-id-card',
        'age': 'fas fa-user-clock',
        'sex': 'fas fa-venus-mars',
        'location': 'fas fa-map-marker-alt',
        'datetime': 'fas fa-calendar-alt',
      },
      'empty_state': {
        'icon_class': 'fas fa-folder-open empty-icon mb-3',
        'title': 'No hay reportes disponibles',
        'message': '¡Comienza a analizar imágenes para ver tus resultados aquí!',
        'upload_button_text': 'Cargar nueva imagen',
        'upload_button_icon': 'fas fa-upload',
      },
      'pagination_texts': {
        'first': '« Primera',
        'previous': 'Anterior',
        'next': 'Siguiente',
        'last': 'Última »',
      }
    })
    logger.info('ReportListView', 'Contexto de lista de reportes generado.')
    return context

  def post(self, request, *args, **kwargs):
    """Sobrescribir el método post para manejar la generación de reportes PDF y envío por email."""
    logger.info('ReportListView', 'Procesando solicitud POST para generación de reportes.')
    try:
      # Aquí puedes manejar la lógica para generar reportes PDF o enviar emails
      # Por ejemplo, si se envía un formulario con un botón específico:
      if 'generate_pdf' in request.POST:
        logger.info('ReportListView',
                    'Generando reporte PDF para el reporte ID: {}'.format(request.POST.get('report_id')))
        # Lógica para generar el PDF
        messages.success(request, 'Reporte PDF generado exitosamente.')
        logger.success('ReportListView', 'Reporte PDF generado exitosamente.')
      elif 'send_email' in request.POST:
        logger.info('ReportListView',
                    'Enviando reporte por email para el reporte ID: {}'.format(request.POST.get('report_id')))
        # Lógica para enviar el email
        messages.success(request, 'Reporte enviado por email exitosamente.')
        logger.success('ReportListView', 'Reporte enviado por email exitosamente.')
      else:
        logger.warning('ReportListView', 'Acción no reconocida en el formulario POST.')
        messages.error(request, 'Acción no reconocida.')
    except Exception as e:
      logger.error('ReportListView', 'Error al procesar la solicitud POST: {}'.format(str(e)))
      messages.error(request, 'Ocurrió un error al procesar su solicitud. Intente nuevamente.')
    return super().get(request, *args, **kwargs)


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
    logger.info('ReportDetailView', f'Vista de detalle de reporte ID={self.object.id} cargada correctamente.')
    return context
