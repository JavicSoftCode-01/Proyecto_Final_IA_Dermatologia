"""
Formulario para la gestión de pacientes en el sistema de dermatología.
"""
from django import forms

from apps.Dermatologia_IA.models import Patient


class PatientForm(forms.ModelForm):
  """
  Formulario para crear y editar pacientes.

  Proporciona una interfaz amigable para gestionar la información
  personal y de contacto de los pacientes.
  """

  class Meta:
    model = Patient
    fields = [
      'first_name',
      'last_name',
      'dni',
      'phone',
      'email',
      'age_approx',
      'sex',
    ]

    labels = {
      'first_name': 'Nombre',
      'last_name': 'Apellido',
      'dni': 'Cédula',
      'phone': 'Teléfono',
      'email': 'Correo Electrónico',
      'age_approx': 'Edad',
      'sex': 'Sexo',
    }

    widgets = {
      'first_name': forms.TextInput(
        attrs={
          'class': 'form-control mb-2',
          'placeholder': 'Ej: Juan Pablo'
        }
      ),
      'last_name': forms.TextInput(
        attrs={
          'class': 'form-control mb-2',
          'placeholder': 'Ej: Pérez Gómez'
        }
      ),
      'dni': forms.TextInput(
        attrs={
          'class': 'form-control mb-2',
          'placeholder': 'Ej: 1234567890'
        }
      ),
      'phone': forms.TextInput(
        attrs={
          'class': 'form-control mb-2',
          'placeholder': 'Ej: 0995336523'
        }
      ),
      'email': forms.EmailInput(
        attrs={
          'class': 'form-control mb-2',
          'placeholder': 'ejemplo@correo.com'
        }
      ),
      'age_approx': forms.NumberInput(
        attrs={
          'class': 'form-control mb-2',
          'min': 0,
          'max': 120,
          'placeholder': 'Edad'
        }
      ),
      'sex': forms.Select(
        attrs={
          'class': 'form-select mb-2'
        }
      ),
    }
