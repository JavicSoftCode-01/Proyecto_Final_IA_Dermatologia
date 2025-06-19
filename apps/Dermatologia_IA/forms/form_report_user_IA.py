"""
Formulario para el registro de imágenes dermatológicas y su asociación con pacientes.
"""

from django import forms

from apps.Dermatologia_IA.models import SkinImage, Patient


class SkinImageForm(forms.ModelForm):
  """
  Formulario para subir y asociar imágenes dermatológicas con pacientes.

  Permite seleccionar un paciente existente y subir una imagen de la lesión
  junto con su localización anatómica.
  """

  patient = forms.ModelChoiceField(
    queryset=Patient.objects.all(),
    required=False,
    widget=forms.Select(
      attrs={
        'class': 'form-select mb-2',
        'id': 'patient_select'
      }
    ),
    label='Paciente',
  )

  class Meta:
    model = SkinImage
    fields = [
      'image',
      'anatom_site_general',
    ]

    labels = {
      'image': 'Imagen de la lesión',
      'anatom_site_general': 'Localización Anatómica',
    }

    widgets = {
      'image': forms.FileInput(
        attrs={
          'class': 'form-control mb-2',
          'accept': 'image/*',
          'id': 'fileInput'
        }
      ),
      'anatom_site_general': forms.Select(
        attrs={
          'class': 'form-select mb-2',
          'id': 'site_select'
        }
      ),
    }

  def clean_image(self):
    image = self.cleaned_data.get('image')
    if image:
      if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise forms.ValidationError(
          'El archivo debe ser una imagen en formato PNG, JPG o JPEG'
        )
      if image.size > 5 * 1024 * 1024:
        raise forms.ValidationError(
          'La imagen no debe exceder los 5MB de tamaño'
        )
    return image
