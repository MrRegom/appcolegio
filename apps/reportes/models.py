from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel


class TipoReporte(BaseModel):
    """Catálogo de tipos de reportes"""
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    modulo = models.CharField(
        max_length=50,
        choices=[
            ('INVENTARIO', 'Inventario'),
            ('COMPRAS', 'Compras'),
            ('SOLICITUDES', 'Solicitudes'),
            ('MOVIMIENTOS', 'Movimientos'),
            ('BAJAS', 'Bajas'),
            ('GENERAL', 'General'),
        ],
        default='GENERAL',
        verbose_name='Módulo'
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')

    class Meta:
        db_table = 'reporte_tipo'
        verbose_name = 'Tipo de Reporte'
        verbose_name_plural = 'Tipos de Reportes'
        ordering = ['modulo', 'codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class ReporteGenerado(BaseModel):
    """Modelo para registrar reportes generados por los usuarios"""
    tipo_reporte = models.ForeignKey(
        TipoReporte,
        on_delete=models.PROTECT,
        related_name='reportes_generados',
        verbose_name='Tipo de Reporte'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='reportes_generados',
        verbose_name='Usuario'
    )
    fecha_generacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Generación')
    fecha_inicio = models.DateField(blank=True, null=True, verbose_name='Fecha Inicio (Filtro)')
    fecha_fin = models.DateField(blank=True, null=True, verbose_name='Fecha Fin (Filtro)')
    parametros = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Parámetros',
        help_text='Parámetros adicionales utilizados para generar el reporte'
    )
    formato = models.CharField(
        max_length=10,
        choices=[
            ('PDF', 'PDF'),
            ('EXCEL', 'Excel'),
            ('CSV', 'CSV'),
            ('HTML', 'HTML'),
        ],
        default='PDF',
        verbose_name='Formato'
    )
    archivo = models.FileField(
        upload_to='reportes/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Archivo Generado'
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')

    class Meta:
        db_table = 'reporte_generado'
        verbose_name = 'Reporte Generado'
        verbose_name_plural = 'Reportes Generados'
        ordering = ['-fecha_generacion']

    def __str__(self):
        return f"{self.tipo_reporte.nombre} - {self.usuario.correo} ({self.fecha_generacion})"


class MovimientoInventario(BaseModel):
    """Modelo para registrar todos los movimientos de inventario"""
    fecha_movimiento = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Movimiento')
    tipo_movimiento = models.CharField(
        max_length=20,
        choices=[
            ('ENTRADA', 'Entrada'),
            ('SALIDA', 'Salida'),
            ('TRASPASO', 'Traspaso'),
            ('AJUSTE', 'Ajuste Positivo'),
            ('AJUSTE_NEG', 'Ajuste Negativo'),
            ('BAJA', 'Baja'),
        ],
        verbose_name='Tipo de Movimiento'
    )

    # Referencias
    activo = models.ForeignKey(
        'activos.Activo',
        on_delete=models.PROTECT,
        related_name='movimientos',
        verbose_name='Activo'
    )
    bodega_origen = models.ForeignKey(
        'bodega.Bodega',
        on_delete=models.PROTECT,
        related_name='movimientos_origen',
        verbose_name='Bodega Origen',
        blank=True,
        null=True
    )
    bodega_destino = models.ForeignKey(
        'bodega.Bodega',
        on_delete=models.PROTECT,
        related_name='movimientos_destino',
        verbose_name='Bodega Destino',
        blank=True,
        null=True
    )

    # Cantidades
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Cantidad'
    )
    stock_anterior = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Stock Anterior'
    )
    stock_nuevo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Stock Nuevo'
    )

    # Referencias a documentos
    documento_referencia = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Documento de Referencia'
    )
    tipo_documento = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Tipo de Documento',
        help_text='Ej: Orden de Compra, Solicitud, Baja, etc.'
    )

    # Usuario y observaciones
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='movimientos_realizados',
        verbose_name='Usuario'
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')

    class Meta:
        db_table = 'reporte_movimiento_inventario'
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        ordering = ['-fecha_movimiento']
        indexes = [
            models.Index(fields=['-fecha_movimiento']),
            models.Index(fields=['activo', '-fecha_movimiento']),
            models.Index(fields=['tipo_movimiento', '-fecha_movimiento']),
        ]

    def __str__(self):
        return f"{self.tipo_movimiento} - {self.activo.codigo} ({self.cantidad}) - {self.fecha_movimiento}"


# ====================================================
# CONSULTAS PARA REPORTES (NO CREA TABLAS)
# ====================================================
# Esta clase contiene métodos estáticos para hacer consultas
# a las tablas de otras apps. NO crea nuevas tablas en la BD.

class ConsultasReportes:
    """
    Clase con métodos estáticos para consultas de reportes.
    NO crea tablas, solo hace consultas a las tablas de otras apps.
    
    Todos los métodos retornan valores numéricos (counts, sums, etc.)
    que se usan para mostrar estadísticas en las cards del dashboard.
    """
    
    # ========== CONSULTAS DE BODEGA ==========
    
    @staticmethod
    def total_articulos():
        """Total de artículos en bodega"""
        from apps.bodega.models import Articulo
        return Articulo.objects.filter(eliminado=False).count()
    
    @staticmethod
    def total_categorias_bodega():
        """Total de categorías de bodega"""
        from apps.bodega.models import Categoria
        return Categoria.objects.filter(eliminado=False).count()
    
    @staticmethod
    def total_movimientos():
        """Total de movimientos de bodega"""
        from apps.bodega.models import Movimiento
        return Movimiento.objects.filter(eliminado=False).count()
    
    @staticmethod
    def total_bodegas():
        """Total de bodegas activas"""
        from apps.bodega.models import Bodega
        return Bodega.objects.filter(eliminado=False, activo=True).count()
    
    @staticmethod
    def stock_total_articulos():
        """Stock total de todos los artículos"""
        from apps.bodega.models import Articulo
        from django.db.models import Sum
        result = Articulo.objects.filter(eliminado=False).aggregate(
            total=Sum('stock_actual')
        )
        return result['total'] or 0
    
    # ========== CONSULTAS DE COMPRAS ==========
    
    @staticmethod
    def total_ordenes_compra():
        """Total de órdenes de compra"""
        from apps.compras.models import OrdenCompra
        return OrdenCompra.objects.filter(eliminado=False).count()
    
    @staticmethod
    def ordenes_pendientes():
        """Órdenes de compra pendientes"""
        from apps.compras.models import OrdenCompra, EstadoOrdenCompra
        estado_pendiente = EstadoOrdenCompra.objects.filter(
            codigo='PENDIENTE',
            eliminado=False
        ).first()
        if estado_pendiente:
            return OrdenCompra.objects.filter(
                eliminado=False,
                estado=estado_pendiente
            ).count()
        return 0
    
    @staticmethod
    def total_recepciones_articulos():
        """Total de recepciones de artículos"""
        from apps.compras.models import RecepcionArticulo
        return RecepcionArticulo.objects.filter(eliminado=False).count()
    
    @staticmethod
    def total_recepciones_activos():
        """Total de recepciones de activos/bienes"""
        from apps.compras.models import RecepcionActivo
        return RecepcionActivo.objects.filter(eliminado=False).count()
    
    @staticmethod
    def total_proveedores():
        """Total de proveedores activos"""
        from apps.compras.models import Proveedor
        return Proveedor.objects.filter(eliminado=False, activo=True).count()
    
    # ========== CONSULTAS DE SOLICITUDES ==========
    
    @staticmethod
    def total_solicitudes():
        """Total de solicitudes"""
        from apps.solicitudes.models import Solicitud
        return Solicitud.objects.filter(eliminado=False).count()
    
    @staticmethod
    def solicitudes_pendientes():
        """Solicitudes pendientes"""
        from apps.solicitudes.models import Solicitud, EstadoSolicitud
        estado_pendiente = EstadoSolicitud.objects.filter(
            codigo='PENDIENTE',
            eliminado=False
        ).first()
        if estado_pendiente:
            return Solicitud.objects.filter(
                eliminado=False,
                estado=estado_pendiente
            ).count()
        return 0
    
    @staticmethod
    def solicitudes_activos():
        """Solicitudes de activos/bienes"""
        from apps.solicitudes.models import Solicitud
        return Solicitud.objects.filter(
            eliminado=False,
            tipo='ACTIVO'
        ).count()
    
    @staticmethod
    def solicitudes_articulos():
        """Solicitudes de artículos"""
        from apps.solicitudes.models import Solicitud
        return Solicitud.objects.filter(
            eliminado=False,
            tipo='ARTICULO'
        ).count()
    
    @staticmethod
    def mis_solicitudes(usuario):
        """Solicitudes del usuario actual"""
        from apps.solicitudes.models import Solicitud
        return Solicitud.objects.filter(
            eliminado=False,
            solicitante=usuario
        ).count()
    
    # ========== CONSULTAS DE ACTIVOS ==========
    
    @staticmethod
    def total_activos():
        """Total de activos activos"""
        from apps.activos.models import Activo
        return Activo.objects.filter(eliminado=False, activo=True).count()
    
    @staticmethod
    def total_categorias_activos():
        """Total de categorías de activos"""
        from apps.activos.models import CategoriaActivo
        return CategoriaActivo.objects.filter(eliminado=False).count()
    
    @staticmethod
    def total_ubicaciones():
        """Total de ubicaciones de activos"""
        from apps.activos.models import Ubicacion
        return Ubicacion.objects.filter(eliminado=False).count()
    
    # ========== CONSULTAS DE BAJAS ==========
    
    @staticmethod
    def total_bajas():
        """Total de bajas de inventario"""
        from apps.bajas_inventario.models import BajaInventario
        return BajaInventario.objects.filter(eliminado=False).count()
    
    # ========== CONSULTAS PARA DASHBOARD OPERATIVO ==========
    
    @staticmethod
    def ordenes_compra_en_proceso():
        """
        Órdenes de compra en proceso (PENDIENTE + APROBADA).
        
        Returns:
            int: Cantidad de órdenes de compra en proceso
        """
        from apps.compras.models import OrdenCompra, EstadoOrdenCompra
        estados_en_proceso = EstadoOrdenCompra.objects.filter(
            codigo__in=['PENDIENTE', 'APROBADA'],
            eliminado=False
        )
        return OrdenCompra.objects.filter(
            eliminado=False,
            estado__in=estados_en_proceso
        ).count()
    
    @staticmethod
    def articulos_stock_critico():
        """
        Artículos con stock crítico (stock_actual < stock_minimo).
        
        Returns:
            int: Cantidad de artículos con stock crítico
        """
        from apps.bodega.repositories import ArticuloRepository
        return ArticuloRepository.get_low_stock().count()
    
    @staticmethod
    def solicitudes_entregadas_mes_actual():
        """
        Solicitudes entregadas en el mes actual.
        
        Returns:
            int: Cantidad de solicitudes entregadas en el mes actual
        """
        from apps.bodega.models import EntregaArticulo
        from django.utils import timezone
        from datetime import datetime
        
        ahora = timezone.now()
        inicio_mes = datetime(ahora.year, ahora.month, 1, tzinfo=ahora.tzinfo)
        
        # Buscar entregas del mes actual con estado COMPLETADA
        from apps.bodega.models import EstadoEntrega
        estado_completada = EstadoEntrega.objects.filter(
            codigo='COMPLETADA',
            eliminado=False
        ).first()
        
        if estado_completada:
            return EntregaArticulo.objects.filter(
                eliminado=False,
                estado=estado_completada,
                fecha_entrega__gte=inicio_mes
            ).count()
        return 0
    
    @staticmethod
    def calcular_tendencia_solicitudes():
        """Calcula el cambio porcentual de solicitudes pendientes"""
        # Por ahora retorna un valor simulado
        # Se puede mejorar con datos históricos
        return -12.5
    
    @staticmethod
    def calcular_tendencia_ordenes():
        """Calcula el cambio porcentual de órdenes en proceso"""
        # Por ahora retorna un valor simulado
        return 0.0
    
    @staticmethod
    def calcular_tendencia_stock_critico():
        """Calcula el cambio porcentual de stock crítico"""
        # Por ahora retorna un valor simulado
        return 0.0
    
    @staticmethod
    def calcular_tendencia_entregas():
        """Calcula el cambio porcentual de entregas del mes"""
        # Por ahora retorna un valor simulado
        return 0.0
    
    @staticmethod
    def tendencia_solicitudes_pendientes(dias: int = 7) -> float:
        """
        Calcula el porcentaje de cambio en solicitudes pendientes.
        
        Args:
            dias: Días hacia atrás para comparar (default: 7)
            
        Returns:
            float: Porcentaje de cambio (positivo = aumento, negativo = disminución)
        """
        from apps.solicitudes.models import Solicitud, EstadoSolicitud
        from django.utils import timezone
        from datetime import timedelta
        
        ahora = timezone.now()
        fecha_comparacion = ahora - timedelta(days=dias)
        
        estado_pendiente = EstadoSolicitud.objects.filter(
            codigo='PENDIENTE',
            eliminado=False
        ).first()
        
        if not estado_pendiente:
            return 0.0
        
        # Solicitudes pendientes actuales
        actual = Solicitud.objects.filter(
            eliminado=False,
            estado=estado_pendiente
        ).count()
        
        # Solicitudes pendientes hace N días (simulado - se puede mejorar con historial)
        # Por ahora retornamos un cálculo basado en la lógica del sistema
        if actual == 0:
            return -100.0  # Si no hay pendientes, es una mejora del 100%
        
        # Simulación: asumimos que si hay pendientes, aumentaron
        # En producción, esto debería comparar con datos históricos reales
        return 100.0 if actual > 0 else 0.0
    
    @staticmethod
    def tendencia_ordenes_compra(dias: int = 30) -> float:
        """
        Calcula el porcentaje de cambio en órdenes de compra en proceso.
        
        Args:
            dias: Días hacia atrás para comparar (default: 30)
            
        Returns:
            float: Porcentaje de cambio
        """
        actual = ConsultasReportes.ordenes_compra_en_proceso()
        
        if actual == 0:
            return 0.0
        
        # Simulación: asumimos que si hay OC en proceso, es actividad positiva
        return 100.0
    
    @staticmethod
    def tendencia_stock_critico(dias: int = 7) -> float:
        """
        Calcula el porcentaje de cambio en artículos con stock crítico.
        
        Args:
            dias: Días hacia atrás para comparar (default: 7)
            
        Returns:
            float: Porcentaje de cambio (negativo = mejora, positivo = empeora)
        """
        actual = ConsultasReportes.articulos_stock_critico()
        
        if actual == 0:
            return -100.0  # Si no hay stock crítico, es una mejora del 100%
        
        # Simulación: si hay stock crítico, asumimos que aumentó
        return 100.0
    
    @staticmethod
    def tendencia_entregas_mes(dias: int = 30) -> float:
        """
        Calcula el porcentaje de cambio en entregas del mes.
        
        Args:
            dias: Días hacia atrás para comparar (default: 30)
            
        Returns:
            float: Porcentaje de cambio
        """
        actual = ConsultasReportes.solicitudes_entregadas_mes_actual()
        
        if actual == 0:
            return 0.0
        
        # Simulación: si hay entregas, asumimos que es actividad positiva
        return 100.0