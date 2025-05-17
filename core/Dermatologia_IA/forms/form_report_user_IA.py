# dermatology/forms.py
from django import forms

from core.Dermatologia_IA.models import SkinImage


class SkinImageForm(forms.ModelForm):
  class Meta:
    model = SkinImage
    fields = ['image', 'age_approx', 'sex', 'anatom_site_general']
    labels = {
      'image': 'Selecciona una imagen de la piel',
      'age_approx': 'Edad Aproximada',
      'sex': 'Sexo',
      'anatom_site_general': 'Localización Anatómica',
    }
    widgets = {
      'image': forms.FileInput(attrs={'class': 'form-control mb-2', 'accept': 'image/*'}),
      'age_approx': forms.NumberInput(attrs={'class': 'form-control mb-2', 'min': 0, 'max': 120}),
      'sex': forms.Select(attrs={'class': 'form-select mb-2'}),
      'anatom_site_general': forms.Select(attrs={'class': 'form-select mb-2'}),
    }
    help_texts = {
      'age_approx': 'Introduce la edad aproximada del paciente.',
      'sex': 'Selecciona el sexo del paciente.',
      'anatom_site_general': 'Selecciona la zona general donde se encuentra la lesión.',
    }
