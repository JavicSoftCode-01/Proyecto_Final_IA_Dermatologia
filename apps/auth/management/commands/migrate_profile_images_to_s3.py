# apps/auth/management/commands/migrate_profile_images_to_s3.py
"""
Comando de Django para migrar imágenes de perfil existentes de almacenamiento local a S3.
"""

import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files import File
from django.conf import settings
from utils.s3_storage import s3_profile_storage
from utils.logger import logger

User = get_user_model()


class Command(BaseCommand):
    help = 'Migra las imágenes de perfil existentes de almacenamiento local a S3'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecuta una simulación sin realizar cambios reales',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Ejecutando en modo simulación (dry-run)')
            )

        # Obtener usuarios con imágenes de perfil
        users_with_images = User.objects.exclude(profile_picture='').exclude(profile_picture__isnull=True)
        total_users = users_with_images.count()

        if total_users == 0:
            self.stdout.write(
                self.style.SUCCESS('No se encontraron usuarios con imágenes de perfil para migrar.')
            )
            return

        self.stdout.write(f'Encontrados {total_users} usuarios con imágenes de perfil.')

        migrated_count = 0
        error_count = 0

        for user in users_with_images:
            try:
                # Verificar si la imagen ya está en S3
                if user.profile_picture.name.startswith('profile_pictures/'):
                    # Es una imagen de S3, skip
                    self.stdout.write(f'Usuario {user.email}: Ya migrado a S3')
                    continue

                # Construir la ruta local de la imagen
                local_path = os.path.join(settings.MEDIA_ROOT, user.profile_picture.name)
                
                if not os.path.exists(local_path):
                    self.stdout.write(
                        self.style.WARNING(f'Usuario {user.email}: Archivo no encontrado en {local_path}')
                    )
                    continue

                if not dry_run:
                    # Abrir el archivo local
                    with open(local_path, 'rb') as file:
                        # Crear un archivo Django
                        django_file = File(file)
                        
                        # Guardar la imagen anterior para eliminarla después
                        old_image_name = user.profile_picture.name
                        
                        # Asignar el nuevo storage y guardar
                        user.profile_picture.save(
                            os.path.basename(local_path),
                            django_file,
                            save=True
                        )
                        
                        # Eliminar el archivo local después de la migración exitosa
                        try:
                            os.remove(local_path)
                            logger.success('MigrateCommand', f'Archivo local eliminado: {local_path}')
                        except OSError as e:
                            logger.warning('MigrateCommand', f'No se pudo eliminar archivo local {local_path}: {str(e)}')

                    self.stdout.write(
                        self.style.SUCCESS(f'Usuario {user.email}: Migrado exitosamente')
                    )
                else:
                    self.stdout.write(f'Usuario {user.email}: Sería migrado desde {local_path}')

                migrated_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Usuario {user.email}: Error al migrar - {str(e)}')
                )
                logger.error('MigrateCommand', f'Error al migrar imagen de {user.email}: {str(e)}')

        # Resumen final
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'Simulación completada: {migrated_count} imágenes serían migradas, {error_count} errores.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Migración completada: {migrated_count} imágenes migradas, {error_count} errores.')
            )
