"""
Comando para configurar categorías de permisos del módulo de solicitudes.

Asocia cada permiso del modelo Solicitud con su módulo funcional correspondiente.

Uso:
    python manage.py setup_permisos_solicitudes
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from apps.solicitudes.models import Solicitud, CategoriaPermiso


class Command(BaseCommand):
    help = 'Configura categorías de permisos del módulo de solicitudes'

    def handle(self, *args, **options):
        """Ejecuta el comando."""
        self.stdout.write(self.style.WARNING('Iniciando configuracion de categorias de permisos...'))

        # Obtener content type de Solicitud
        content_type = ContentType.objects.get_for_model(Solicitud)

        # Mapeo de permisos a módulos
        permisos_config = {
            # GESTIÓN
            'gestionar_solicitudes': {'modulo': CategoriaPermiso.Modulo.GESTION, 'orden': 1},
            'aprobar_solicitudes': {'modulo': CategoriaPermiso.Modulo.GESTION, 'orden': 2},
            'rechazar_solicitudes': {'modulo': CategoriaPermiso.Modulo.GESTION, 'orden': 3},
            'despachar_solicitudes': {'modulo': CategoriaPermiso.Modulo.GESTION, 'orden': 4},
            'ver_todas_solicitudes': {'modulo': CategoriaPermiso.Modulo.GESTION, 'orden': 5},
            'editar_cualquier_solicitud': {'modulo': CategoriaPermiso.Modulo.GESTION, 'orden': 6},
            'eliminar_cualquier_solicitud': {'modulo': CategoriaPermiso.Modulo.GESTION, 'orden': 7},

            # SOLICITUD ARTÍCULOS
            'crear_solicitud_articulos': {'modulo': CategoriaPermiso.Modulo.SOLICITUD_ARTICULOS, 'orden': 1},
            'ver_solicitudes_articulos': {'modulo': CategoriaPermiso.Modulo.SOLICITUD_ARTICULOS, 'orden': 2},

            # SOLICITUD BIENES
            'crear_solicitud_bienes': {'modulo': CategoriaPermiso.Modulo.SOLICITUD_BIENES, 'orden': 1},
            'ver_solicitudes_bienes': {'modulo': CategoriaPermiso.Modulo.SOLICITUD_BIENES, 'orden': 2},

            # MIS SOLICITUDES
            'ver_mis_solicitudes': {'modulo': CategoriaPermiso.Modulo.MIS_SOLICITUDES, 'orden': 1},
            'editar_mis_solicitudes': {'modulo': CategoriaPermiso.Modulo.MIS_SOLICITUDES, 'orden': 2},
            'eliminar_mis_solicitudes': {'modulo': CategoriaPermiso.Modulo.MIS_SOLICITUDES, 'orden': 3},
        }

        # Contadores
        creados = 0
        actualizados = 0
        errores = 0

        # Procesar cada permiso
        for codename, config in permisos_config.items():
            try:
                # Buscar el permiso
                permiso = Permission.objects.filter(
                    content_type=content_type,
                    codename=codename
                ).first()

                if not permiso:
                    self.stdout.write(
                        self.style.WARNING(f'[!] Permiso no encontrado: {codename}')
                    )
                    errores += 1
                    continue

                # Crear o actualizar CategoriaPermiso
                categoria, created = CategoriaPermiso.objects.update_or_create(
                    permiso=permiso,
                    defaults={
                        'modulo': config['modulo'],
                        'orden': config['orden'],
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[+] Creado: {permiso.name} -> {categoria.get_modulo_display()}'
                        )
                    )
                    creados += 1
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[*] Actualizado: {permiso.name} -> {categoria.get_modulo_display()}'
                        )
                    )
                    actualizados += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'[!] Error procesando {codename}: {str(e)}')
                )
                errores += 1

        # Resumen
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'[OK] Categorias creadas: {creados}'))
        self.stdout.write(self.style.SUCCESS(f'[OK] Categorias actualizadas: {actualizados}'))

        if errores > 0:
            self.stdout.write(self.style.ERROR(f'[ERROR] Errores: {errores}'))

        self.stdout.write('=' * 60)
        self.stdout.write(
            self.style.SUCCESS('\n[OK] Configuracion completada exitosamente!')
        )
