"""
Management command para inicializar datos básicos del módulo de bodega.

Crea operaciones y tipos de movimiento necesarios para el funcionamiento del sistema.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.bodega.models import Operacion, TipoMovimiento


class Command(BaseCommand):
    help = 'Inicializa datos básicos del módulo de bodega (Operaciones y Tipos de Movimiento)'

    def handle(self, *args, **options):
        """Ejecuta la inicialización de datos."""
        self.stdout.write(self.style.SUCCESS('Inicializando datos basicos de bodega...'))

        with transaction.atomic():
            # Crear operaciones básicas
            self._crear_operaciones()

            # Crear tipos de movimiento básicos
            self._crear_tipos_movimiento()

        self.stdout.write(self.style.SUCCESS('OK - Datos basicos de bodega inicializados correctamente'))

    def _crear_operaciones(self):
        """Crea operaciones básicas (ENTRADA y SALIDA)."""
        operaciones = [
            {
                'codigo': 'ENTRADA',
                'nombre': 'Entrada',
                'tipo': 'ENTRADA',
                'descripcion': 'Operación de entrada de artículos al inventario',
                'activo': True,
            },
            {
                'codigo': 'SALIDA',
                'nombre': 'Salida',
                'tipo': 'SALIDA',
                'descripcion': 'Operación de salida de artículos del inventario',
                'activo': True,
            },
        ]

        creadas = 0
        for op_data in operaciones:
            operacion, created = Operacion.objects.get_or_create(
                codigo=op_data['codigo'],
                defaults=op_data
            )
            if created:
                creadas += 1
                self.stdout.write(f'  + Operacion creada: {operacion.codigo} - {operacion.nombre}')
            else:
                self.stdout.write(f'  - Operacion ya existe: {operacion.codigo}')

        self.stdout.write(self.style.SUCCESS(f'\nOperaciones creadas: {creadas}/{len(operaciones)}'))

    def _crear_tipos_movimiento(self):
        """Crea tipos de movimiento básicos."""
        tipos_movimiento = [
            {
                'codigo': 'RECEPCION',
                'nombre': 'Recepción de Compra',
                'descripcion': 'Movimiento generado por recepción de orden de compra',
                'activo': True,
            },
            {
                'codigo': 'ENTREGA',
                'nombre': 'Entrega',
                'descripcion': 'Movimiento generado por entrega de artículos',
                'activo': True,
            },
            {
                'codigo': 'AJUSTE_POSITIVO',
                'nombre': 'Ajuste Positivo',
                'descripcion': 'Ajuste de inventario - aumento de stock',
                'activo': True,
            },
            {
                'codigo': 'AJUSTE_NEGATIVO',
                'nombre': 'Ajuste Negativo',
                'descripcion': 'Ajuste de inventario - disminución de stock',
                'activo': True,
            },
            {
                'codigo': 'TRASPASO_ENTRADA',
                'nombre': 'Traspaso - Entrada',
                'descripcion': 'Entrada por traspaso entre bodegas',
                'activo': True,
            },
            {
                'codigo': 'TRASPASO_SALIDA',
                'nombre': 'Traspaso - Salida',
                'descripcion': 'Salida por traspaso entre bodegas',
                'activo': True,
            },
        ]

        creados = 0
        for tipo_data in tipos_movimiento:
            tipo, created = TipoMovimiento.objects.get_or_create(
                codigo=tipo_data['codigo'],
                defaults=tipo_data
            )
            if created:
                creados += 1
                self.stdout.write(f'  + Tipo movimiento creado: {tipo.codigo} - {tipo.nombre}')
            else:
                self.stdout.write(f'  - Tipo movimiento ya existe: {tipo.codigo}')

        self.stdout.write(self.style.SUCCESS(f'\nTipos de movimiento creados: {creados}/{len(tipos_movimiento)}'))
