# core/Dermatologia_IA/forms/form_report_user_IA.py

from django import forms

from core.Dermatologia_IA.models import SkinImage


class SkinImageForm(forms.ModelForm):
  class Meta:
    model = SkinImage
    fields = [
      'first_name', 'last_name', 'dni', 'phone', 'email',
      'image', 'age_approx', 'sex', 'anatom_site_general'
    ]
    labels = {
      'first_name': 'Nombre',
      'last_name': 'Apellido',
      'dni': 'DNI',
      'phone': 'Teléfono',
      'email': 'Correo Electrónico',
      'image': 'Selecciona una imagen de la piel',
      'age_approx': 'Edad Aproximada',
      'sex': 'Sexo',
      'anatom_site_general': 'Localización Anatómica',
    }
    widgets = {
      'first_name': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'Nombre'}),
      'last_name': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'Apellido'}),
      'dni': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'DNI'}),
      'phone': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'Teléfono'}),
      'email': forms.EmailInput(attrs={'class': 'form-control mb-2', 'placeholder': 'Correo electrónico'}),
      'image': forms.FileInput(attrs={'class': 'form-control mb-2', 'accept': 'image/*'}),
      'age_approx': forms.NumberInput(attrs={'class': 'form-control mb-2', 'min': 0, 'max': 120}),
      'sex': forms.Select(attrs={'class': 'form-select mb-2'}),
      'anatom_site_general': forms.Select(attrs={'class': 'form-select mb-2'}),
    }
    help_texts = {
      'first_name': 'Nombre completo del paciente.',
      'last_name': 'Apellido del paciente.',
      'dni': 'Documento de identidad.',
      'phone': 'Número de teléfono de contacto.',
      'email': 'Correo electrónico del paciente.',
      'age_approx': 'Introduce la edad aproximada del paciente.',
      'sex': 'Selecciona el sexo del paciente.',
      'anatom_site_general': 'Selecciona la zona general donde se encuentra la lesión.',
    }
