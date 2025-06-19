"""
Modelo de usuario personalizado para la aplicación auth.
Este modelo utiliza el correo electrónico como identificador principal
y simplifica la gestión de usuarios al no incluir permisos ni grupos.
El modelo incluye campos para información personal, de contacto y una imagen de perfil.
"""

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.core.exceptions import ValidationError

from utils.validators import (
  validate_email,
  validate_full_name,
  validate_dni,
  validate_address_and_city,
  validate_phone,
  validate_profile_picture
)
from apps.auth.services.aws.s3_storage import s3_profile_storage


class CustomUserManager(BaseUserManager):
  """
  Gestor personalizado para la creación de usuarios.
  Simplifica el proceso de creación manteniendo solo la funcionalidad esencial.
  """

  def create_user(self, email, password=None, **extra_fields):
    if not email:
      raise ValueError('El correo electrónico es obligatorio')

    user = self.model(
      email=self.normalize_email(email),
      **extra_fields
    )
    user.set_password(password)
    user.is_active = True
    user.save(using=self._db)
    return user

  def create_superuser(self, email, password=None, **extra_fields):
    extra_fields['is_staff'] = True
    extra_fields['is_superuser'] = True
    return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser):
  """
  Modelo de usuario personalizado que usa email como identificador principal.

  Este modelo representa a los usuarios del sistema, almacenando su información
  personal y de contacto. No incluye manejo de permisos para mantener la simplicidad.
  """

  email = models.EmailField(
    'Correo electrónico',
    unique=True,
    max_length=50,
    validators=[validate_email],
    error_messages={
      'unique': 'Ya existe un usuario con este correo electrónico.'
    }
  )

  first_name = models.CharField(
    'Nombres',
    max_length=50,
    validators=[validate_full_name]
  )

  last_name = models.CharField(
    'Apellidos',
    max_length=50,
    validators=[validate_full_name]
  )

  dni = models.CharField(
    'Cédula',
    max_length=10,
    unique=True,
    blank=True,
    null=True,
    validators=[validate_dni],
    error_messages={
      'unique': 'Ya existe un usuario con esta cédula.'
    }
  )

  address = models.CharField(
    'Dirección',
    max_length=255,
    blank=True,
    null=True,
    validators=[validate_address_and_city]
  )

  city = models.CharField(
    'Ciudad',
    max_length=255,
    blank=True,
    null=True,
    validators=[validate_address_and_city]
  )

  phone = models.CharField(
    'Teléfono',
    max_length=20,
    unique=True,
    blank=True,
    null=True,
    validators=[validate_phone],
    error_messages={
      'unique': 'Ya existe un usuario con este número de teléfono.'
    }
  )

  profile_picture = models.ImageField(
    'Foto de perfil',
    storage=s3_profile_storage,
    blank=True,
    null=True,
    validators=[validate_profile_picture]
  )

  created_at = models.DateTimeField(
    'Fecha de creación',
    auto_now_add=True
  )

  updated_at = models.DateTimeField(
    'Fecha de actualización',
    auto_now=True
  )

  is_active = models.BooleanField(default=True)
  is_staff = models.BooleanField(default=False)
  is_superuser = models.BooleanField(default=False)

  objects = CustomUserManager()
  USERNAME_FIELD = 'email'
  REQUIRED_FIELDS = ['first_name', 'last_name']

  def clean(self):
    if not self.email:
      raise ValidationError({'email': 'El correo electrónico es obligatorio'})

    if not self.first_name or not self.last_name:
      raise ValidationError('Los nombres y apellidos son obligatorios')

  def save(self, *args, **kwargs):
    try:
      if self.pk:
        old_user = User.objects.get(pk=self.pk)
        if old_user.profile_picture and self.profile_picture != old_user.profile_picture:
          # Eliminar la imagen anterior de S3
          old_user.profile_picture.storage.delete(old_user.profile_picture.name)
    except User.DoesNotExist:
      pass

    super().save(*args, **kwargs)

  def delete(self, *args, **kwargs):
    if self.profile_picture:
      self.profile_picture.storage.delete(self.profile_picture.name)
    super().delete(*args, **kwargs)

  def get_full_name(self):
    return f"{self.first_name} {self.last_name}"

  def __str__(self):
    return f"{self.get_full_name()} <{self.email}>"

  class Meta:
    verbose_name = 'Usuario'
    verbose_name_plural = 'Usuarios'
    ordering = ['last_name', 'first_name']
