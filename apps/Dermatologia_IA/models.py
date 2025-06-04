from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from utils.validators import (
  validate_full_name,
  validate_dni,
  validate_phone,
  validate_email,
  validate_profile_picture
)


class Patient(models.Model):
  """
  Modelo que representa a un paciente en el sistema de dermatología.

  Este modelo almacena la información personal y demográfica básica
  de los pacientes que serán atendidos en el sistema.
  """

  first_name = models.CharField(
    max_length=50,
    validators=[validate_full_name],
  )

  last_name = models.CharField(
    max_length=50,
    validators=[validate_full_name],
  )

  dni = models.CharField(
    'Cédula',
    max_length=10,
    unique=True,
    validators=[validate_dni],
    error_messages={
      'unique': 'Ya existe un usuario con esta cédula.'
    }
  )

  phone = models.CharField(
    'Teléfono',
    max_length=20,
    unique=True,
    validators=[validate_phone],
    error_messages={
      'unique': 'Ya existe un usuario con este número de teléfono.'
    }
  )

  email = models.EmailField(
    'Correo electrónico',
    unique=True,
    max_length=50,
    validators=[validate_email],
    error_messages={
      'unique': 'Ya existe un usuario con este correo electrónico.'
    }
  )

  age_approx = models.PositiveIntegerField(
    validators=[
      MinValueValidator(0, "La edad no puede ser negativa"),
      MaxValueValidator(110, "La edad máxima permitida es 110 años")
    ],
  )

  SEX_CHOICES = [
    ('female', 'Femenino'),
    ('male', 'Masculino'),
  ]

  sex = models.CharField(
    max_length=10,
    choices=SEX_CHOICES,
  )

  def get_full_name(self):
    """Retorna el nombre completo del paciente"""
    return f"{self.first_name} {self.last_name}"

  def __str__(self):
    """Representación en string del paciente"""
    return f"{self.get_full_name()} (CI: {self.dni})"

  class Meta:
    verbose_name = 'Paciente'
    verbose_name_plural = 'Pacientes'
    ordering = ['last_name', 'first_name']


class SkinImage(models.Model):
  """
  Modelo que representa una imagen dermatológica y su diagnóstico IA.

  Almacena las imágenes de lesiones cutáneas junto con sus metadatos,
  resultados del análisis de IA y ubicación anatómica.
  """

  # Relación con el paciente
  patient = models.ForeignKey(
    Patient,
    on_delete=models.CASCADE,
    related_name='consultas',
  )

  # Campos de imagen y timestamp
  image = models.ImageField(
    upload_to='skin_images/',
    validators=[validate_profile_picture]
  )

  uploaded_at = models.DateTimeField(
    auto_now_add=True,
    blank=True,
    null=True,
  )

  created_at = models.DateTimeField(
    auto_now_add=True,
    blank=True,
    null=True,
  )

  # Campos de procesamiento y diagnóstico IA
  processed = models.BooleanField(
    default=False,
    blank=True,
    null=True,
  )

  condition = models.CharField(
    max_length=50,
    blank=True,
    null=True,
    help_text="Condición dermatológica detectada por la IA"
  )

  confidence = models.FloatField(
    blank=True,
    null=True,
    validators=[
      MinValueValidator(0.0, "La confianza no puede ser negativa"),
      MaxValueValidator(1.0, "La confianza no puede ser mayor a 1")
    ],
  )

  gradcam_path = models.CharField(
    max_length=255,
    blank=True,
    null=True,
    help_text="Ruta a la imagen de visualización GradCAM"
  )

  ai_report = models.TextField(
    blank=True,
    null=True,
  )

  ai_treatment = models.TextField(
    blank=True,
    null=True,
  )

  # Ubicación anatómica
  ANATOM_SITE_CHOICES = [
    ('abdomen', 'Abdomen'),
    ('acral', 'Acral (Palmas, Plantas, Dedos)'),
    ('anterior_torso', 'Torso Anterior'),
    ('back', 'Espalda'),
    ('chest', 'Pecho'),
    ('ear', 'Oreja'),
    ('face', 'Cara'),
    ('foot', 'Pie'),
    ('genital', 'Genital'),
    ('hand', 'Mano'),
    ('head_neck', 'Cabeza/Cuello'),
    ('lateral_torso', 'Torso Lateral'),
    ('lower_extremity', 'Extremidad Inferior'),
    ('neck', 'Cuello'),
    ('oral_genital', 'Oral/Genital'),
    ('palms_soles', 'Palmas/Plantas'),
    ('posterior_torso', 'Torso Posterior'),
    ('scalp', 'Cuero Cabelludo'),
    ('trunk', 'Tronco (General)'),
    ('upper_extremity', 'Extremidad Superior'),
    ('unknown', 'Desconocida/Otra'),
  ]

  anatom_site_general = models.CharField(
    max_length=50,
    choices=ANATOM_SITE_CHOICES,
    default='Desconocida',
  )

  def get_status(self):
    """Retorna el estado actual del análisis de la imagen"""
    if self.condition:
      return self.condition
    return 'Procesada' if self.processed else 'Pendiente'

  def __str__(self):
    """Representación en string de la consulta"""
    return (f"Consulta de {self.patient.get_full_name()} - "
            f"({self.get_status()})")

  class Meta:
    verbose_name = 'Imagen Dermatológica'
    verbose_name_plural = 'Imágenes Dermatológicas'
    ordering = ['-created_at']
