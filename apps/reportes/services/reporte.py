"""
Service Layer para gestion de reportes dinamicos.

Contiene la logica de negocio para obtener informacion de reportes,
sus filtros y configuracion. Sigue Clean Architecture estricta.
"""
from typing import Dict, Any, List, Optional
from django.utils import timezone
from datetime import datetime, timedelta


class ReporteService:
    """
    Service para logica de negocio de Reportes.
    
    Orquesta la obtencion de informacion de reportes disponibles,
    sus filtros y configuracion, separando completamente la logica
    de negocio de la presentacion.
    
    Sigue el patron Service Layer de Clean Architecture.
    """

    # Catalogo de reportes disponibles con su configuracion
    REPORTES_DISPONIBLES = {
        'articulos_sin_movimiento': {
            'codigo': 'articulos_sin_movimiento',
            'nombre': 'Articulos sin Movimiento',
            'modulo': 'bodega',
            'descripcion': 'Lista de articulos que no han tenido movimientos en el periodo seleccionado',
            'filtros': {
                'desde': {
                    'tipo': 'date',
                    'label': 'Fecha de Inicio',
                    'requerido': False,
                    'default': None
                },
                'hasta': {
                    'tipo': 'date',
                    'label': 'Fecha de Termino',
                    'requerido': False,
                    'default': None
                },
                'bodega_id': {
                    'tipo': 'select',
                    'label': 'Bodega',
                    'requerido': False,
                    'opciones': 'bodegas'
                },
                'categoria_id': {
                    'tipo': 'select',
                    'label': 'Categoria',
                    'requerido': False,
                    'opciones': 'categorias'
                }
            },
            'url_name': 'reportes:articulos_sin_movimiento',
            'service_class': 'ArticulosSinMovimientoService'
        },
        'oc_atrasadas_por_proveedor': {
            'codigo': 'oc_atrasadas_por_proveedor',
            'nombre': 'OC Atrasadas por Proveedor',
            'modulo': 'compras',
            'descripcion': 'Ordenes de compra atrasadas agrupadas por proveedor',
            'filtros': {
                'proveedor_id': {
                    'tipo': 'select',
                    'label': 'Proveedor',
                    'requerido': False,
                    'opciones': 'proveedores'
                },
                'bodega_id': {
                    'tipo': 'select',
                    'label': 'Bodega destino',
                    'requerido': False,
                    'opciones': 'bodegas'
                }
            },
            'url_name': 'reportes:oc_atrasadas_por_proveedor',
            'service_class': 'OcAtrasadasPorProveedorService'
        }
    }

    @staticmethod
    def obtener_reportes_por_modulo(modulo: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de reportes disponibles, opcionalmente filtrados por modulo.
        
        Args:
            modulo: Codigo del modulo ('bodega', 'compras', etc.) o None para todos
            
        Returns:
            Lista de diccionarios con informacion de reportes
        """
        if modulo:
            return [
                reporte for reporte in ReporteService.REPORTES_DISPONIBLES.values()
                if reporte['modulo'] == modulo
            ]
        return list(ReporteService.REPORTES_DISPONIBLES.values())

    @staticmethod
    def obtener_reporte_por_codigo(codigo: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuracion de un reporte especifico por su codigo.
        
        Args:
            codigo: Codigo del reporte
            
        Returns:
            Diccionario con configuracion del reporte o None si no existe
        """
        return ReporteService.REPORTES_DISPONIBLES.get(codigo)

    @staticmethod
    def obtener_filtros_para_reporte(codigo: str) -> Dict[str, Any]:
        """
        Obtiene la configuracion de filtros para un reporte especifico.
        
        Args:
            codigo: Codigo del reporte
            
        Returns:
            Diccionario con configuracion de filtros
        """
        reporte = ReporteService.obtener_reporte_por_codigo(codigo)
        if reporte:
            return reporte.get('filtros', {})
        return {}

    @staticmethod
    def obtener_opciones_para_filtro(filtro_tipo: str) -> List[Dict[str, Any]]:
        """
        Obtiene las opciones para un tipo de filtro (bodegas, categorias, etc.).
        
        Args:
            filtro_tipo: Tipo de opciones ('bodegas', 'categorias', 'proveedores')
            
        Returns:
            Lista de diccionarios con opciones
        """
        from apps.bodega.models import Bodega, Categoria
        from apps.compras.models import Proveedor

        if filtro_tipo == 'bodegas':
            return [
                {'id': b.id, 'nombre': f'{b.codigo} - {b.nombre}'}
                for b in Bodega.objects.filter(eliminado=False, activo=True).order_by('codigo')
            ]
        elif filtro_tipo == 'categorias':
            return [
                {'id': c.id, 'nombre': f'{c.codigo} - {c.nombre}'}
                for c in Categoria.objects.filter(eliminado=False).order_by('codigo')
            ]
        elif filtro_tipo == 'proveedores':
            return [
                {'id': p.id, 'nombre': f'{p.rut} - {p.razon_social}'}
                for p in Proveedor.objects.filter(eliminado=False, activo=True).order_by('razon_social')
            ]
        return []

