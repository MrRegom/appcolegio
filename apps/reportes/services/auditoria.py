"""
Service Layer para el módulo de auditoría de actividades.

Contiene la lógica de negocio para obtener y filtrar actividades del sistema
siguiendo el principio de Single Responsibility (SOLID) y Clean Architecture estricta.

La vista solo orquesta, toda la lógica de negocio está aquí.
"""
from typing import Dict, Any, List, Optional
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q

from apps.bodega.models import Movimiento, EntregaArticulo
from apps.solicitudes.models import Solicitud
from apps.activos.models import MovimientoActivo
from apps.compras.models import OrdenCompra


class AuditoriaService:
    """
    Service para lógica de negocio de Auditoría de Actividades.

    Orquesta las consultas y filtros necesarios para la vista de auditoría,
    separando completamente la lógica de negocio de la presentación.

    Sigue el patrón Service Layer de Clean Architecture.
    """

    TIPOS_ACTIVIDAD = {
        'movimiento': 'Movimiento de Inventario',
        'entrega': 'Entrega de Artículos',
        'solicitud': 'Solicitud',
        'movimiento_activo': 'Movimiento de Activo',
        'orden_compra': 'Orden de Compra',
    }

    @staticmethod
    def obtener_actividades(
        tipo: Optional[str] = None,
        usuario_id: Optional[int] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        modulo: Optional[str] = None,
        buscar: Optional[str] = None,
        limite: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Obtiene una lista combinada de actividades del sistema con filtros.

        Args:
            tipo: Tipo de actividad ('movimiento', 'entrega', 'solicitud', etc.)
            usuario_id: ID del usuario que realizó la actividad
            fecha_desde: Fecha inicial del rango
            fecha_hasta: Fecha final del rango
            modulo: Módulo del sistema ('bodega', 'compras', 'solicitudes', 'activos')
            buscar: Texto para búsqueda general
            limite: Número máximo de actividades a retornar

        Returns:
            Lista de diccionarios con detalles de actividad ordenados por fecha descendente
        """
        actividades = []

        # Filtros comunes
        filtros_base = {}
        if fecha_desde:
            filtros_base['fecha_desde'] = fecha_desde
        if fecha_hasta:
            filtros_base['fecha_hasta'] = fecha_hasta

        # Obtener movimientos de inventario (bodega)
        if not tipo or tipo == 'movimiento':
            if not modulo or modulo == 'bodega':
                movimientos = AuditoriaService._obtener_movimientos(
                    usuario_id=usuario_id,
                    buscar=buscar,
                    **filtros_base
                )
                for mov in movimientos[:limite]:
                    actividades.append({
                        'tipo': 'movimiento',
                        'modulo': 'bodega',
                        'titulo': f'Movimiento de {mov.articulo.nombre[:50]}',
                        'descripcion': f'{mov.tipo.nombre} - {mov.cantidad} {mov.articulo.unidad_medida.simbolo if mov.articulo.unidad_medida else ""}',
                        'usuario': mov.usuario.get_full_name() or mov.usuario.username,
                        'usuario_id': mov.usuario.id,
                        'fecha': mov.fecha_creacion,
                        'icono': 'ri-arrow-left-right-line',
                        'color': 'primary',
                        'url_detalle': f'/bodega/movimientos/{mov.id}/',
                        'codigo': mov.articulo.codigo,
                    })

        # Obtener entregas de artículos (bodega)
        if not tipo or tipo == 'entrega':
            if not modulo or modulo == 'bodega':
                entregas = AuditoriaService._obtener_entregas(
                    usuario_id=usuario_id,
                    buscar=buscar,
                    **filtros_base
                )
                for entrega in entregas[:limite]:
                    actividades.append({
                        'tipo': 'entrega',
                        'modulo': 'bodega',
                        'titulo': f'Entrega #{entrega.numero}',
                        'descripcion': f'Entregada por {entrega.entregado_por.get_full_name() or entrega.entregado_por.username}',
                        'usuario': entrega.entregado_por.get_full_name() or entrega.entregado_por.username,
                        'usuario_id': entrega.entregado_por.id,
                        'fecha': entrega.fecha_entrega,
                        'icono': 'ri-truck-line',
                        'color': 'success',
                        'url_detalle': f'/bodega/entregas/{entrega.id}/',
                        'codigo': entrega.numero,
                    })

        # Obtener solicitudes
        if not tipo or tipo == 'solicitud':
            if not modulo or modulo == 'solicitudes':
                solicitudes = AuditoriaService._obtener_solicitudes(
                    usuario_id=usuario_id,
                    buscar=buscar,
                    **filtros_base
                )
                for sol in solicitudes[:limite]:
                    actividades.append({
                        'tipo': 'solicitud',
                        'modulo': 'solicitudes',
                        'titulo': f'Solicitud #{sol.numero}',
                        'descripcion': f'{sol.get_tipo_display()} - {sol.estado.nombre}',
                        'usuario': sol.solicitante.get_full_name() or sol.solicitante.username,
                        'usuario_id': sol.solicitante.id,
                        'fecha': sol.fecha_creacion,
                        'icono': 'ri-file-text-line',
                        'color': 'info',
                        'url_detalle': f'/solicitudes/{sol.id}/',
                        'codigo': sol.numero,
                    })

        # Obtener movimientos de activos
        if not tipo or tipo == 'movimiento_activo':
            if not modulo or modulo == 'activos':
                movimientos_activos = AuditoriaService._obtener_movimientos_activos(
                    usuario_id=usuario_id,
                    buscar=buscar,
                    **filtros_base
                )
                for mov_act in movimientos_activos[:limite]:
                    actividades.append({
                        'tipo': 'movimiento_activo',
                        'modulo': 'activos',
                        'titulo': f'Movimiento de Activo {mov_act.activo.codigo}',
                        'descripcion': f'{mov_act.tipo_movimiento.nombre if mov_act.tipo_movimiento else "Movimiento"}',
                        'usuario': mov_act.usuario_registro.get_full_name() if mov_act.usuario_registro else 'Sistema',
                        'usuario_id': mov_act.usuario_registro.id if mov_act.usuario_registro else None,
                        'fecha': mov_act.fecha_creacion,
                        'icono': 'ri-box-3-line',
                        'color': 'warning',
                        'url_detalle': f'/activos/movimientos/{mov_act.id}/',
                        'codigo': mov_act.activo.codigo,
                    })

        # Obtener órdenes de compra
        if not tipo or tipo == 'orden_compra':
            if not modulo or modulo == 'compras':
                ordenes = AuditoriaService._obtener_ordenes_compra(
                    usuario_id=usuario_id,
                    buscar=buscar,
                    **filtros_base
                )
                for oc in ordenes[:limite]:
                    actividades.append({
                        'tipo': 'orden_compra',
                        'modulo': 'compras',
                        'titulo': f'Orden de Compra #{oc.numero}',
                        'descripcion': f'{oc.estado.nombre if oc.estado else "Sin estado"} - {oc.proveedor.razon_social if oc.proveedor else "Sin proveedor"}',
                        'usuario': oc.solicitante.get_full_name() if oc.solicitante else 'Sistema',
                        'usuario_id': oc.solicitante.id if oc.solicitante else None,
                        'fecha': oc.fecha_creacion,
                        'icono': 'ri-shopping-cart-line',
                        'color': 'danger',
                        'url_detalle': f'/compras/ordenes/{oc.id}/',
                        'codigo': oc.numero,
                    })

        # Ordenar por fecha (más reciente primero)
        actividades.sort(key=lambda x: x['fecha'], reverse=True)

        # Aplicar límite final
        return actividades[:limite]

    @staticmethod
    def _obtener_movimientos(
        usuario_id: Optional[int] = None,
        buscar: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[Movimiento]:
        """Obtiene movimientos de inventario con filtros."""
        queryset = Movimiento.objects.filter(
            eliminado=False
        ).select_related('articulo', 'tipo', 'usuario', 'articulo__unidad_medida')

        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)

        if buscar:
            queryset = queryset.filter(
                Q(articulo__nombre__icontains=buscar) |
                Q(articulo__codigo__icontains=buscar) |
                Q(tipo__nombre__icontains=buscar)
            )

        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__lte=fecha_hasta)

        return list(queryset.order_by('-fecha_creacion'))

    @staticmethod
    def _obtener_entregas(
        usuario_id: Optional[int] = None,
        buscar: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[EntregaArticulo]:
        """Obtiene entregas de artículos con filtros."""
        queryset = EntregaArticulo.objects.filter(
            eliminado=False
        ).select_related('tipo', 'estado', 'entregado_por', 'bodega_origen')

        if usuario_id:
            queryset = queryset.filter(entregado_por_id=usuario_id)

        if buscar:
            queryset = queryset.filter(
                Q(numero__icontains=buscar) |
                Q(tipo__nombre__icontains=buscar)
            )

        if fecha_desde:
            queryset = queryset.filter(fecha_entrega__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_entrega__lte=fecha_hasta)

        return list(queryset.order_by('-fecha_entrega'))

    @staticmethod
    def _obtener_solicitudes(
        usuario_id: Optional[int] = None,
        buscar: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[Solicitud]:
        """Obtiene solicitudes con filtros."""
        queryset = Solicitud.objects.filter(
            eliminado=False
        ).select_related('solicitante', 'estado')

        if usuario_id:
            queryset = queryset.filter(solicitante_id=usuario_id)

        if buscar:
            queryset = queryset.filter(
                Q(numero__icontains=buscar) |
                Q(descripcion__icontains=buscar)
            )

        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__lte=fecha_hasta)

        return list(queryset.order_by('-fecha_creacion'))

    @staticmethod
    def _obtener_movimientos_activos(
        usuario_id: Optional[int] = None,
        buscar: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[MovimientoActivo]:
        """Obtiene movimientos de activos con filtros."""
        queryset = MovimientoActivo.objects.filter(
            eliminado=False
        ).select_related('activo', 'tipo_movimiento', 'usuario_registro')

        if usuario_id:
            queryset = queryset.filter(usuario_registro_id=usuario_id)

        if buscar:
            queryset = queryset.filter(
                Q(activo__codigo__icontains=buscar) |
                Q(activo__nombre__icontains=buscar)
            )

        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__lte=fecha_hasta)

        return list(queryset.order_by('-fecha_creacion'))

    @staticmethod
    def _obtener_ordenes_compra(
        usuario_id: Optional[int] = None,
        buscar: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[OrdenCompra]:
        """Obtiene órdenes de compra con filtros."""
        queryset = OrdenCompra.objects.filter(
            eliminado=False
        ).select_related('proveedor', 'solicitante', 'estado', 'bodega_destino')

        if usuario_id:
            queryset = queryset.filter(solicitante_id=usuario_id)

        if buscar:
            queryset = queryset.filter(
                Q(numero__icontains=buscar) |
                Q(proveedor__nombre__icontains=buscar)
            )

        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__lte=fecha_hasta)

        return list(queryset.order_by('-fecha_creacion'))

    @staticmethod
    def obtener_estadisticas_actividades() -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de actividades.

        Returns:
            Diccionario con estadísticas por tipo y módulo
        """
        ahora = timezone.now()
        ultimos_30_dias = ahora - timedelta(days=30)

        return {
            'total_movimientos': Movimiento.objects.filter(eliminado=False).count(),
            'total_entregas': EntregaArticulo.objects.filter(eliminado=False).count(),
            'total_solicitudes': Solicitud.objects.filter(eliminado=False).count(),
            'total_movimientos_activos': MovimientoActivo.objects.filter(eliminado=False).count(),
            'total_ordenes_compra': OrdenCompra.objects.filter(eliminado=False).count(),
            'movimientos_30_dias': Movimiento.objects.filter(
                eliminado=False,
                fecha_creacion__gte=ultimos_30_dias
            ).count(),
            'entregas_30_dias': EntregaArticulo.objects.filter(
                eliminado=False,
                fecha_entrega__gte=ultimos_30_dias
            ).count(),
            'solicitudes_30_dias': Solicitud.objects.filter(
                eliminado=False,
                fecha_creacion__gte=ultimos_30_dias
            ).count(),
        }

