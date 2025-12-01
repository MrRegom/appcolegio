"""
Service Layer para el módulo de páginas/dashboard.

Contiene la lógica de negocio del dashboard siguiendo el principio de
Single Responsibility (SOLID) y Clean Architecture estricta.

La vista solo orquesta, toda la lógica de negocio está aquí.
"""
from typing import Dict, Any, List
from django.utils import timezone
from datetime import timedelta, datetime
from apps.reportes.models import ConsultasReportes
from apps.bodega.models import Articulo, EntregaArticulo, Movimiento
from apps.bodega.repositories import ArticuloRepository
from apps.solicitudes.models import Solicitud


class DashboardService:
    """
    Service para lógica de negocio del Dashboard.
    
    Orquesta las consultas y cálculos necesarios para el dashboard,
    separando completamente la lógica de negocio de la presentación.
    
    Sigue el patrón Service Layer de Clean Architecture.
    """
    
    @staticmethod
    def obtener_metricas_principales() -> Dict[str, Any]:
        """
        Obtiene las métricas principales del dashboard operativo.
        
        Returns:
            Dict con las métricas principales y sus tendencias.
        """
        return {
            # Card 1: Solicitudes Pendientes (CRÍTICO)
            'solicitudes_pendientes': ConsultasReportes.solicitudes_pendientes(),
            'solicitudes_change': ConsultasReportes.tendencia_solicitudes_pendientes(),
            
            # Card 2: Órdenes de Compra en Proceso (ALTO)
            'ordenes_en_proceso': ConsultasReportes.ordenes_compra_en_proceso(),
            'ordenes_change': ConsultasReportes.tendencia_ordenes_compra(),
            
            # Card 3: Artículos Stock Crítico (CRÍTICO)
            'articulos_stock_critico': ConsultasReportes.articulos_stock_critico(),
            'stock_critico_change': ConsultasReportes.tendencia_stock_critico(),
            
            # Card 4: Solicitudes Entregadas Mes Actual (MEDIO)
            'solicitudes_entregadas_mes': ConsultasReportes.solicitudes_entregadas_mes_actual(),
            'entregas_change': ConsultasReportes.tendencia_entregas_mes(),
        }
    
    @staticmethod
    def obtener_metricas_complementarias() -> Dict[str, Any]:
        """
        Obtiene métricas complementarias para gráficos y tablas.
        
        Returns:
            Dict con métricas complementarias.
        """
        return {
            'total_articulos': ConsultasReportes.total_articulos(),
            'stock_total': ConsultasReportes.stock_total_articulos(),
            'total_activos': ConsultasReportes.total_activos(),
            'total_movimientos': ConsultasReportes.total_movimientos(),
        }
    
    @staticmethod
    def obtener_datos_graficos() -> Dict[str, Any]:
        """
        Obtiene datos para gráficos de actividad.
        
        Returns:
            Dict con datos para gráficos.
        """
        now = timezone.now()
        meses_data = []
        movimientos_data = []
        solicitudes_data = []
        
        total_movimientos = ConsultasReportes.total_movimientos()
        total_solicitudes = ConsultasReportes.total_solicitudes()
        
        for i in range(6, 0, -1):
            fecha = now - timedelta(days=30 * i)
            meses_data.append(fecha.strftime("%b '%y"))
            movimientos_data.append(int(total_movimientos / 6))
            solicitudes_data.append(int(total_solicitudes / 6))
        
        return {
            'meses_data': meses_data,
            'movimientos_data': movimientos_data,
            'solicitudes_data': solicitudes_data,
        }
    
    @staticmethod
    def obtener_datos_grafico_articulos_mas_usados() -> Dict[str, Any]:
        """
        Obtiene datos para el gráfico de artículos más utilizados.
        
        Returns:
            Dict con nombres y cantidades de artículos más usados.
        """
        from django.db.models import Count
        import json
        
        articulos_mas_usados = Articulo.objects.filter(
            eliminado=False,
            movimientos__eliminado=False
        ).annotate(
            total_movimientos=Count('movimientos')
        ).order_by('-total_movimientos')[:10]
        
        articulos_nombres = json.dumps([art.codigo[:20] for art in articulos_mas_usados])
        articulos_cantidades = json.dumps([art.total_movimientos for art in articulos_mas_usados])
        
        return {
            'articulos_mas_usados': articulos_mas_usados,
            'articulos_nombres': articulos_nombres,
            'articulos_cantidades': articulos_cantidades,
        }
    
    @staticmethod
    def obtener_ultimos_productos(limite: int = 10) -> List[Articulo]:
        """
        Obtiene los últimos productos creados.
        
        Args:
            limite: Cantidad de productos a retornar
            
        Returns:
            Lista de artículos
        """
        return list(
            Articulo.objects.filter(
                eliminado=False
            ).select_related(
                'categoria', 'ubicacion_fisica', 'unidad_medida'
            ).order_by('-fecha_creacion')[:limite]
        )
    
    @staticmethod
    def obtener_productos_top_stock(limite: int = 10) -> List[Articulo]:
        """
        Obtiene los productos con mayor stock.
        
        Args:
            limite: Cantidad de productos a retornar
            
        Returns:
            Lista de artículos
        """
        return list(
            Articulo.objects.filter(
                eliminado=False
            ).select_related(
                'categoria', 'ubicacion_fisica', 'unidad_medida'
            ).order_by('-stock_actual')[:limite]
        )
    
    @staticmethod
    def obtener_articulos_stock_bajo(limite: int = 10) -> List[Articulo]:
        """
        Obtiene artículos con stock bajo.
        
        Args:
            limite: Cantidad de artículos a retornar
            
        Returns:
            Lista de artículos con stock bajo
        """
        return list(ArticuloRepository.get_low_stock()[:limite])
    
    @staticmethod
    def obtener_ultimas_entregas(limite: int = 10) -> List[EntregaArticulo]:
        """
        Obtiene las últimas entregas de inventario.
        
        Args:
            limite: Cantidad de entregas a retornar
            
        Returns:
            Lista de entregas
        """
        return list(
            EntregaArticulo.objects.filter(
                eliminado=False
            ).select_related(
                'tipo', 'estado', 'entregado_por', 'bodega_origen'
            ).prefetch_related(
                'detalles__articulo'
            ).order_by('-fecha_entrega')[:limite]
        )
    
    @staticmethod
    def obtener_ultimos_movimientos(limite: int = 10) -> List[Movimiento]:
        """
        Obtiene los últimos movimientos de bodega.
        
        Args:
            limite: Cantidad de movimientos a retornar
            
        Returns:
            Lista de movimientos
        """
        return list(
            Movimiento.objects.filter(
                eliminado=False
            ).select_related(
                'articulo', 'tipo', 'usuario'
            ).order_by('-fecha_creacion')[:limite]
        )
    
    @staticmethod
    def obtener_actividades_recientes(limite: int = 2) -> List[Dict[str, Any]]:
        """
        Obtiene actividades recientes combinando movimientos, entregas y solicitudes.
        
        Args:
            limite: Cantidad de actividades a retornar
            
        Returns:
            Lista de diccionarios con información de actividades
        """
        actividades = []
        
        # Agregar movimientos recientes
        ultimos_movimientos = DashboardService.obtener_ultimos_movimientos(limite=5)
        for mov in ultimos_movimientos:
            actividades.append({
                'tipo': 'movimiento',
                'titulo': f'Movimiento de {mov.articulo.nombre[:30]}',
                'descripcion': f'{mov.tipo.nombre} - {mov.cantidad} {mov.articulo.unidad_medida.simbolo if mov.articulo.unidad_medida else ""}',
                'usuario': mov.usuario.get_full_name() or mov.usuario.username,
                'fecha': mov.fecha_creacion,
                'icono': 'ri-arrow-left-right-line',
                'color': 'primary'
            })
        
        # Agregar entregas recientes
        ultimas_entregas = DashboardService.obtener_ultimas_entregas(limite=5)
        for entrega in ultimas_entregas:
            actividades.append({
                'tipo': 'entrega',
                'titulo': f'Entrega #{entrega.numero}',
                'descripcion': f'Entregada por {entrega.entregado_por.get_full_name() or entrega.entregado_por.username}',
                'usuario': entrega.entregado_por.get_full_name() or entrega.entregado_por.username,
                'fecha': entrega.fecha_entrega,
                'icono': 'ri-truck-line',
                'color': 'success'
            })
        
        # Agregar solicitudes recientes
        solicitudes_recientes = Solicitud.objects.filter(
            eliminado=False
        ).select_related('solicitante', 'estado').order_by('-fecha_creacion')[:5]
        
        for sol in solicitudes_recientes:
            actividades.append({
                'tipo': 'solicitud',
                'titulo': f'Solicitud #{sol.numero}',
                'descripcion': f'{sol.get_tipo_display()} - {sol.estado.nombre}',
                'usuario': sol.solicitante.get_full_name() or sol.solicitante.username,
                'fecha': sol.fecha_creacion,
                'icono': 'ri-file-text-line',
                'color': 'info'
            })
        
        # Ordenar por fecha (más reciente primero) y tomar las más recientes
        actividades.sort(key=lambda x: x['fecha'], reverse=True)
        return actividades[:limite]
