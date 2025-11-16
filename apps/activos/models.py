"""
Modelos del módulo de activos.

Este módulo gestiona el inventario de activos del colegio, incluyendo:
- Catálogos: Categorías, Estados, Ubicaciones, Marcas, Talleres, Proveniencias
- Gestión de Activos: Registro individual de cada activo
- Movimientos: Historial de movimientos y trazabilidad de activos

Todos los modelos heredan de BaseModel para mantener auditoría y soft delete.
Convención de nomenclatura: todas las tablas tienen prefijo 'tba_'.
"""
from __future__ import annotations

from typing import Any
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User

from core.models import BaseModel

# Constante del RBD del establecimiento
RBD_ESTABLECIMIENTO = '1437'


class CategoriaActivo(BaseModel):
    """
    Catálogo de categorías de activos.

    Hereda de BaseModel para mantener consistencia con el resto del proyecto
    y aprovechar soft delete, campos de auditoría y estado activo/inactivo.
    """
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    sigla = models.CharField(
        max_length=3,
        unique=True,
        verbose_name='Sigla',
        help_text='Sigla de 3 caracteres para generación automática de códigos de activos (ej: NTB, LCD, ESC)'
    )
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')

    class Meta:
        db_table = 'tba_activo_categoria'
        verbose_name = 'Categoría de Activo'
        verbose_name_plural = 'Categorías de Activos'
        ordering = ['codigo']

    def __str__(self) -> str:
        """Representación en string del objeto."""
        return f"{self.codigo} - {self.nombre}"

class EstadoActivo(BaseModel):
    """
    Catálogo de estados de activos.

    Hereda de BaseModel para soft delete y auditoría.
    """
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    color = models.CharField(
        max_length=7,
        default='#6c757d',
        verbose_name='Color (Hex)',
        help_text='Color en formato hexadecimal para visualización'
    )
    es_inicial = models.BooleanField(default=False, verbose_name='Estado Inicial')
    permite_movimiento = models.BooleanField(default=True, verbose_name='Permite Movimiento')

    class Meta:
        db_table = 'tba_activo_estado'
        verbose_name = 'Estado de Activo'
        verbose_name_plural = 'Estados de Activos'
        ordering = ['codigo']

    def __str__(self) -> str:
        """Representación en string del objeto."""
        return f"{self.codigo} - {self.nombre}"


class Ubicacion(BaseModel):
    """
    Catálogo de ubicaciones físicas para activos.

    Hereda de BaseModel para soft delete y auditoría.
    """
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')

    class Meta:
        db_table = 'tba_activo_ubicacion'
        verbose_name = 'Ubicación'
        verbose_name_plural = 'Ubicaciones'
        ordering = ['codigo']

    def __str__(self) -> str:
        """Representación en string del objeto."""
        return f"{self.codigo} - {self.nombre}"


class Proveniencia(BaseModel):
    """
    Catálogo de proveniencias de activos.

    Indica el origen o procedencia del activo (compra, donación, etc.)
    """
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')

    class Meta:
        db_table = 'tba_activo_proveniencia'
        verbose_name = 'Proveniencia'
        verbose_name_plural = 'Proveniencias'
        ordering = ['codigo']

    def __str__(self) -> str:
        """Representación en string del objeto."""
        return f"{self.codigo} - {self.nombre}"

class Marca(BaseModel):
    """
    Catálogo de marcas de activos.

    Hereda de BaseModel para soft delete y auditoría.
    """
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')

    class Meta:
        db_table = 'tba_activo_marca'
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['codigo']

    def __str__(self) -> str:
        """Representación en string del objeto."""
        return f"{self.codigo} - {self.nombre}"


class Taller(BaseModel):
    """
    Catálogo de talleres de servicio para activos.

    Hereda de BaseModel para soft delete y auditoría.
    """
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    ubicacion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Ubicación Física',
        help_text='Ubicación física del taller'
    )
    responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='talleres_responsable',
        verbose_name='Responsable',
        blank=True,
        null=True,
        help_text='Persona responsable del taller'
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observaciones'
    )

    class Meta:
        db_table = 'tba_activo_taller'
        verbose_name = 'Taller'
        verbose_name_plural = 'Talleres'
        ordering = ['codigo']

    def __str__(self) -> str:
        """Representación en string del objeto."""
        return f"{self.codigo} - {self.nombre}"

class TipoMovimientoActivo(BaseModel):
    """
    Catálogo de tipos de movimiento de activos.

    Hereda de BaseModel para soft delete y auditoría.
    """
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')

    class Meta:
        db_table = 'tba_activo_tipo_movimiento'
        verbose_name = 'Tipo de Movimiento de Activo'
        verbose_name_plural = 'Tipos de Movimiento de Activos'
        ordering = ['codigo']

    def __str__(self) -> str:
        """Representación en string del objeto."""
        return f"{self.codigo} - {self.nombre}"


class Activo(BaseModel):
    """
    Modelo principal para gestionar activos/productos del inventario.

    Hereda de BaseModel para aprovechar soft delete, auditoría automática
    y campos de control (activo, eliminado, fecha_creacion, fecha_actualizacion).
    """
    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código/SKU')
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    categoria = models.ForeignKey(
        CategoriaActivo,
        on_delete=models.PROTECT,
        related_name='activos',
        verbose_name='Categoría'
    )
    estado = models.ForeignKey(
        EstadoActivo,
        on_delete=models.PROTECT,
        related_name='activos',
        verbose_name='Estado'
    )
    # Información del producto
    marca = models.ForeignKey(
        Marca,
        on_delete=models.PROTECT,
        related_name='activos',
        blank=True,
        null=True,
        verbose_name='Marca'
    )
    lote = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Lote',
        help_text='Requerido si el activo requiere lote'
    )
    numero_serie = models.CharField(max_length=100, blank=True, null=True, verbose_name='Número de Serie')
    codigo_barras = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        verbose_name='Código de Barras',
        help_text='Código de barras del producto (dejar vacío para auto-generar desde el código)'
    )
    # Precios
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
        verbose_name='Precio Unitario'
    )

    def _generar_codigo(self) -> str:
        """
        Genera automáticamente el código del activo según formato CCCNNNNN-NNN.

        Formato:
        - CCC: Sigla de la categoría (3 caracteres)
        - NNNNN: RBD del establecimiento en 5 dígitos (con ceros a la izquierda)
        - NNN: Correlativo de 3 dígitos para esa categoría (empezando en 001)

        Ejemplos:
        - NTB01437-001: Primer portátil
        - LCD01437-023: Monitor LCD número 23

        Returns:
            str: Código generado en formato CCCNNNNN-NNN
        """
        # Obtener la sigla de la categoría
        sigla: str = self.categoria.sigla.upper()

        # Formatear RBD a 5 dígitos con ceros a la izquierda
        rbd_formateado: str = RBD_ESTABLECIMIENTO.zfill(5)

        # Obtener el último correlativo de esta categoría
        ultimo_activo = Activo.objects.filter(
            categoria=self.categoria,
            eliminado=False
        ).exclude(pk=self.pk).order_by('-codigo').first()

        if ultimo_activo and ultimo_activo.codigo:
            # Extraer el correlativo del último código (últimos 3 dígitos después del guión)
            try:
                ultimo_correlativo: int = int(ultimo_activo.codigo.split('-')[-1])
                nuevo_correlativo: int = ultimo_correlativo + 1
            except (ValueError, IndexError):
                # Si hay error al parsear, empezar desde 1
                nuevo_correlativo: int = 1
        else:
            # Primer activo de esta categoría
            nuevo_correlativo: int = 1

        # Formatear correlativo a 3 dígitos
        correlativo_formateado: str = str(nuevo_correlativo).zfill(3)

        # Generar código final
        codigo_generado: str = f"{sigla}{rbd_formateado}-{correlativo_formateado}"

        return codigo_generado

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Guarda el activo en la base de datos.

        Auto-genera el código si no se proporciona, usando el formato CCCNNNNN-NNN.
        Auto-genera el código de barras si no se proporciona.

        Args:
            *args: Argumentos posicionales para save()
            **kwargs: Argumentos nombrados para save()
        """
        # Generar código automáticamente si no existe
        if not self.codigo:
            self.codigo = self._generar_codigo()

        # Generar código de barras desde el código/SKU si no existe
        if not self.codigo_barras and self.codigo:
            codigo_limpio: str = self.codigo.replace('-', '').replace('_', '').upper()[:12]
            self.codigo_barras = f"COD{codigo_limpio}"

        super().save(*args, **kwargs)

    class Meta:
        db_table = 'tba_activo'
        verbose_name = 'Activo'
        verbose_name_plural = 'Activos'
        ordering = ['codigo']
        permissions = [
            ('gestionar_inventario', 'Puede gestionar inventario de activos'),
            ('ajustar_inventario', 'Puede realizar ajustes de inventario'),
            ('ver_reportes_inventario', 'Puede ver reportes de inventario'),
            ('importar_activos', 'Puede importar activos masivamente'),
            ('exportar_activos', 'Puede exportar listado de activos'),
        ]

    def __str__(self) -> str:
        """Representación en string del objeto."""
        return f"{self.codigo} - {self.nombre}"


class MovimientoActivo(BaseModel):
    """
    Modelo para rastrear movimientos individuales de activos.
    Cada activo es único y se rastrea individualmente (no por cantidades).
    """
    activo = models.ForeignKey(
        Activo,
        on_delete=models.PROTECT,
        related_name='movimientos_activo',
        verbose_name='Activo'
    )
    estado_nuevo = models.ForeignKey(
        EstadoActivo,
        on_delete=models.PROTECT,
        related_name='movimientos_estado',
        verbose_name='Nuevo Estado',
        help_text='Estado al que se cambiará el activo',
        null=True,
        blank=True
    )
    tipo_movimiento = models.ForeignKey(
        TipoMovimientoActivo,
        on_delete=models.PROTECT,
        related_name='movimientos',
        verbose_name='Tipo de Movimiento',
        blank=True,
        null=True
    )
    ubicacion_destino = models.ForeignKey(
        Ubicacion,
        on_delete=models.PROTECT,
        related_name='movimientos_destino',
        verbose_name='Ubicación Destino',
        blank=True,
        null=True,
        help_text='Ubicación física donde se encuentra el activo'
    )
    taller = models.ForeignKey(
        Taller,
        on_delete=models.PROTECT,
        related_name='movimientos_taller',
        verbose_name='Taller',
        blank=True,
        null=True,
        help_text='Taller asociado al movimiento, si aplica'
    )
    responsable = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='activos_responsable',
        verbose_name='Responsable',
        blank=True,
        null=True,
        help_text='Usuario responsable del activo'
    )

    proveniencia = models.ForeignKey(
        'Proveniencia',
        on_delete=models.PROTECT,
        related_name='movimientos',
        verbose_name='Proveniencia',
        blank=True,
        null=True,
        help_text='Origen o procedencia del activo'
    )

    id_baja_inventario = models.ForeignKey(
        'bajas_inventario.BajaInventario',
        on_delete=models.PROTECT,
        related_name='movimientos_activo',
        blank=True,
        null=True,
        verbose_name='ID Baja de Inventario',
        help_text='ID de la baja de inventario asociada, si aplica'
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observaciones'
    )
    usuario_registro = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='movimientos_registrados',
        verbose_name='Usuario que Registró'
    )

    class Meta:
        db_table = 'tba_activo_movimiento'
        verbose_name = 'Movimiento de Activo'
        verbose_name_plural = 'Movimientos de Activos'
        ordering = ['-fecha_creacion']
        permissions = [
            ('registrar_movimiento', 'Puede registrar movimientos de activos'),
            ('ver_historial_movimientos', 'Puede ver historial de movimientos'),
        ]

    def __str__(self) -> str:
        """Representación en string del movimiento."""
        ubicacion: str = self.ubicacion_destino.nombre if self.ubicacion_destino else 'Sin ubicación'
        responsable: str = self.responsable.get_full_name() if self.responsable else 'Sin responsable'
        return f"{self.activo.codigo} - {ubicacion} - {responsable}"
