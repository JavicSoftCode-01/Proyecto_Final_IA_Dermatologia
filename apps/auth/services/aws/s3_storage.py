"""
Configuración personalizada para el almacenamiento en Amazon S3.
Maneja específicamente las imágenes de perfil de usuario.
"""

import os
import uuid

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

from utils.logger import logger


@deconstructible
class S3ProfilePictureStorage(Storage):
  """
  Storage personalizado para manejar imágenes de perfil en S3.
  """

  def __init__(self):
    self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    self.region_name = settings.AWS_S3_REGION_NAME
    self.aws_access_key_id = settings.AWS_ACCESS_KEY_ID
    self.aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
    self.folder = 'profile_pictures'

    if not self.aws_access_key_id or not self.aws_secret_access_key:
      raise ValueError("AWS credentials not found in settings")

    self.s3_client = boto3.client(
      's3',
      aws_access_key_id=self.aws_access_key_id,
      aws_secret_access_key=self.aws_secret_access_key,
      region_name=self.region_name
    )

  def _save(self, name, content):
    try:
      file_extension = os.path.splitext(name)[1]
      unique_filename = f"{uuid.uuid4()}{file_extension}"
      s3_key = f"{self.folder}/{unique_filename}"

      self.s3_client.upload_fileobj(
        content,
        self.bucket_name,
        s3_key,
        ExtraArgs={
          'ContentType': self._get_content_type(file_extension),
          'ACL': 'public-read'
        }
      )
      logger.success('S3Storage', f'Imagen subida exitosamente: {s3_key}')
      return s3_key

    except ClientError as e:
      logger.error('S3Storage', f'Error al subir imagen a S3: {str(e)}')
      raise Exception(f"Error al subir imagen: {str(e)}")

  def _open(self, name, mode='rb'):
    try:
      response = self.s3_client.get_object(Bucket=self.bucket_name, Key=name)
      return ContentFile(response['Body'].read())
    except ClientError as e:
      logger.error('S3Storage', f'Error al abrir imagen desde S3: {str(e)}')
      return None

  def delete(self, name):
    try:
      if name:
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=name)
        logger.success('S3Storage', f'Imagen eliminada exitosamente: {name}')
        return True
    except ClientError as e:
      logger.error('S3Storage', f'Error al eliminar imagen de S3: {str(e)}')
      return False

  def exists(self, name):
    try:
      self.s3_client.head_object(Bucket=self.bucket_name, Key=name)
      return True
    except ClientError:
      return False

  def url(self, name):
    if not name:
      return None
    return f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{name}"

  def _get_content_type(self, file_extension):
    content_types = {
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.png': 'image/png',
    }
    return content_types.get(file_extension.lower(), 'application/octet-stream')


s3_profile_storage = S3ProfilePictureStorage()
