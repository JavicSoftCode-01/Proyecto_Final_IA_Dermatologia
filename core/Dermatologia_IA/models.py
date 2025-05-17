from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class SkinImage(models.Model):
  image = models.ImageField(upload_to='skin_images/')
  uploaded_at = models.DateTimeField(auto_now_add=True)
  processed = models.BooleanField(default=False)
  condition = models.CharField(max_length=50, blank=True, null=True)
  location = models.CharField(max_length=50, blank=True, null=True)
  confidence = models.FloatField(blank=True, null=True)
  gradcam_path = models.CharField(max_length=255, blank=True, null=True)
  ai_report = models.TextField(blank=True, null=True)
  ai_treatment = models.TextField(blank=True, null=True)

  # Edad aproximada (campo numérico requerido)
  age_approx = models.PositiveIntegerField(
    blank=False,
    null=False,
    validators=[MinValueValidator(0), MaxValueValidator(120)],  # Validación básica
    help_text="Edad aproximada del paciente (0-120)."
  )

  # Sexo (campo categórico requerido)
  SEX_CHOICES = [
    ('female', 'Femenino'),
    ('male', 'Masculino'),
    ('unknown', 'Desconocido/No especificado'),
  ]
  sex = models.CharField(
    max_length=10,
    choices=SEX_CHOICES,
    blank=False,
    null=False,
    default='unknown',
    help_text="Sexo del paciente."
  )

  # Localización anatómica general (campo categórico requerido)
  ANATOM_SITE_CHOICES = [
    ('abdomen', 'Abdomen'),
    ('acral', 'Acral (Palmas, Plantas, Dedos)'),
    ('anterior torso', 'Torso Anterior'),
    ('back', 'Espalda'),
    ('chest', 'Pecho'),
    ('ear', 'Oreja'),
    ('face', 'Cara'),
    ('foot', 'Pie'),
    ('genital', 'Genital'),
    ('hand', 'Mano'),
    ('head/neck', 'Cabeza/Cuello'),
    ('lateral torso', 'Torso Lateral'),
    ('lower extremity', 'Extremidad Inferior'),
    ('neck', 'Cuello'),
    ('oral/genital', 'Oral/Genital'),
    ('palms/soles', 'Palmas/Plantas'),
    ('posterior torso', 'Torso Posterior'),
    ('scalp', 'Cuero Cabelludo'),
    ('trunk', 'Tronco (General)'),  # Usar 'trunk' como lo vio el preprocesador
    ('unknown', 'Desconocida/Otra'),  # El preprocesador aprendió 'unknown'
    ('upper extremity', 'Extremidad Superior'),
  ]
  anatom_site_general = models.CharField(
    max_length=50,  # Asegúrate de que sea suficiente para el valor más largo
    choices=ANATOM_SITE_CHOICES,
    blank=False,
    null=False,
    default='unknown',  # Valor por defecto
    help_text="Localización anatómica general de la lesión."
  )

  def __str__(self):
    status = self.condition or ('Procesada' if self.processed else 'Pendiente')
    # Incluir metadatos en la representación string
    age_str = f"Edad: {self.age_approx}" if self.age_approx is not None else "Edad: ?"
    sex_str = f"Sexo: {self.get_sex_display()}" if self.sex else "Sexo: ?"
    site_str = f"Loc: {self.get_anatom_site_general_display()}" if self.anatom_site_general else "Loc: ?"
    return f"Imagen {self.id} ({status}) - {age_str}, {sex_str}, {site_str}"
