# apps/auth/models.py

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from utils.validators import (
  validate_email, validate_full_name, validate_dni,
  validate_address_and_city, validate_phone, validate_profile_picture
)


class UserManager(BaseUserManager):
  def create_user(self, email, password=None, **extra_fields):
    if not email:
      raise ValueError('El correo electrónico debe ser proporcionado')
    email = self.normalize_email(email)
    user = self.model(email=email, **extra_fields)
    user.set_password(password)
    user.is_active = True  # ¡IMPORTANTE! Asegura que el usuario esté activo por defecto
    user.save(using=self._db)
    return user

  def create_superuser(self, email, password=None, **extra_fields):
    extra_fields.setdefault('is_staff', True)
    extra_fields.setdefault('is_superuser', True)
    extra_fields.setdefault('is_active', True)  # También para superusuarios
    return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
  email = models.EmailField(
    'Correo electrónico',
    unique=True,
    max_length=50,
    validators=[validate_email]
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
    validators=[validate_dni]
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
    validators=[validate_phone]
  )
  profile_picture = models.ImageField(
    'Foto de perfil',
    upload_to='profile_pictures/',
    blank=True,
    null=True,
    default='static/img/avatar.jpg',
    validators=[validate_profile_picture]
  )
  created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
  updated_at = models.DateTimeField('Fecha de actualización', auto_now=True)
  groups = models.ManyToManyField(
    'auth.Group',
    verbose_name='Grupos',
    blank=True,
    help_text='Los grupos a los que pertenece este usuario.',
    related_name='custom_user_groups',
    related_query_name='custom_user'
  )

  user_permissions = models.ManyToManyField(
    'auth.Permission',
    verbose_name='Permisos de usuario',
    blank=True,
    help_text='Permisos específicos para este usuario.',
    related_name='custom_user_permissions',
    related_query_name='custom_user'
  )

  username = None
  USERNAME_FIELD = 'email'
  REQUIRED_FIELDS = ['first_name', 'last_name']

  objects = UserManager()

  def save(self, *args, **kwargs):
    if not self.email:
      raise ValueError('El correo electrónico debe ser proporcionado')
    super().save(*args, **kwargs)

  def __str__(self):
    return f"{self.first_name} {self.last_name} <{self.email}>"

  class Meta:
    verbose_name = 'Usuario'
    verbose_name_plural = 'Usuarios'
