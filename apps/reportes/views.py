from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from datetime import datetime
from django.http import HttpRequest, HttpResponse
from .models import TipoReporte, ReporteGenerado, MovimientoInventario
from apps.activos.models import MovimientoActivo, Activo, Ubicacion
from apps.bodega.models import Bodega, Categoria
from apps.compras.models import Proveedor

# Servicios y exportadores
from apps.reportes.services.bodega import ArticulosSinMovimientoService
from apps.reportes.services.compras import OcAtrasadasPorProveedorService
from apps.reportes.exporters.pdf import export_pdf
from apps.reportes.exporters.xlsx import export_xlsx


@login_required
def lista_reportes(request):
    """Vista para listar tipos de reportes disponibles"""
    tipos_reportes = TipoReporte.objects.filter(activo=True).order_by('modulo', 'codigo')

    context = {
        'tipos_reportes': tipos_reportes,
        'titulo': 'Reportes Disponibles'
    }
    return render(request, 'reportes/lista_reportes.html', context)


@login_required
def historial_reportes(request):
    """Vista para ver el historial de reportes generados"""
    reportes = ReporteGenerado.objects.select_related(
        'tipo_reporte', 'usuario'
    ).order_by('-fecha_generacion')[:100]

    context = {
        'reportes': reportes,
        'titulo': 'Historial de Reportes'
    }
    return render(request, 'reportes/historial_reportes.html', context)


@login_required
def reporte_inventario_actual(request):
    """Vista para ver el reporte de ubicación actual de activos"""
    ubicaciones = Ubicacion.objects.select_related(
        'activo', 'ubicacion', 'responsable', 'activo__categoria', 'activo__estado'
    ).all()

    # Estadísticas
    total_items = ubicaciones.count()
    total_activos = Activo.objects.filter(activo=True).count()
    total_valor = Activo.objects.filter(activo=True).aggregate(
        total=Sum('precio_unitario')
    )['total'] or 0

    context = {
        'ubicaciones': ubicaciones,
        'total_items': total_items,
        'total_activos': total_activos,
        'total_valor': total_valor,
        'titulo': 'Ubicación Actual de Activos'
    }
    return render(request, 'reportes/inventario_actual.html', context)


@login_required
def reporte_movimientos(request):
    """Vista para ver el reporte de movimientos de inventario"""
    # Por defecto, últimos 30 días
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if not fecha_desde:
        fecha_desde = timezone.now() - timedelta(days=30)
    if not fecha_hasta:
        fecha_hasta = timezone.now()

    movimientos = MovimientoInventario.objects.select_related(
        'activo', 'bodega_origen', 'bodega_destino', 'usuario'
    ).filter(
        fecha_movimiento__gte=fecha_desde,
        fecha_movimiento__lte=fecha_hasta
    )

    # Estadísticas por tipo
    stats_tipo = movimientos.values('tipo_movimiento').annotate(
        total=Count('id')
    ).order_by('-total')

    context = {
        'movimientos': movimientos,
        'stats_tipo': stats_tipo,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'titulo': 'Movimientos de Inventario'
    }
    return render(request, 'reportes/movimientos.html', context)


@login_required
def dashboard_reportes(request, app=None):
    """
    Dashboard de reportes con cards organizadas por app.
    
    Args:
        app: 'bodega', 'compras', 'solicitudes', 'activos', 'bajas' o None para todas
    """
    from .models import ConsultasReportes
    
    # Si no se especifica app, mostrar todas
    if not app:
        app = 'todas'
    
    # Validar que la app sea válida
    apps_validas = ['bodega', 'compras', 'solicitudes', 'activos', 'bajas', 'todas']
    if app not in apps_validas:
        app = 'todas'
    
    context = {
        'app': app,
        'titulo': f'Reportes - {app.capitalize() if app != "todas" else "General"}'
    }
    
    # Consultas según la app seleccionada
    if app == 'bodega' or app == 'todas':
        context['stats_bodega'] = {
            'total_articulos': ConsultasReportes.total_articulos(),
            'total_categorias': ConsultasReportes.total_categorias_bodega(),
            'total_movimientos': ConsultasReportes.total_movimientos(),
            'total_bodegas': ConsultasReportes.total_bodegas(),
            'stock_total': ConsultasReportes.stock_total_articulos(),
        }
    
    if app == 'compras' or app == 'todas':
        context['stats_compras'] = {
            'total_ordenes': ConsultasReportes.total_ordenes_compra(),
            'ordenes_pendientes': ConsultasReportes.ordenes_pendientes(),
            'recepciones_articulos': ConsultasReportes.total_recepciones_articulos(),
            'recepciones_activos': ConsultasReportes.total_recepciones_activos(),
            'total_proveedores': ConsultasReportes.total_proveedores(),
        }
    
    if app == 'solicitudes' or app == 'todas':
        context['stats_solicitudes'] = {
            'total_solicitudes': ConsultasReportes.total_solicitudes(),
            'solicitudes_pendientes': ConsultasReportes.solicitudes_pendientes(),
            'solicitudes_activos': ConsultasReportes.solicitudes_activos(),
            'solicitudes_articulos': ConsultasReportes.solicitudes_articulos(),
            'mis_solicitudes': ConsultasReportes.mis_solicitudes(request.user),
        }
    
    if app == 'activos' or app == 'todas':
        context['stats_activos'] = {
            'total_activos': ConsultasReportes.total_activos(),
            'total_categorias': ConsultasReportes.total_categorias_activos(),
            'total_ubicaciones': ConsultasReportes.total_ubicaciones(),
        }
    
    if app == 'bajas' or app == 'todas':
        context['stats_bajas'] = {
            'total_bajas': ConsultasReportes.total_bajas(),
        }
    
    return render(request, 'reportes/dashboard.html', context)


# ==================== NUEVOS REPORTES ====================


@login_required
def articulos_sin_movimiento(request: HttpRequest) -> HttpResponse:
    """
    En pantalla/PDF/XLSX de artículos sin movimiento.
    Filtros: desde, hasta, bodega_id, categoria_id
    """
    fmt = request.GET.get("format", "html")
    desde_str = request.GET.get("desde")
    hasta_str = request.GET.get("hasta")
    bodega_id = request.GET.get("bodega_id")
    categoria_id = request.GET.get("categoria_id")

    # Defaults: últimos 30 días
    hoy = timezone.now().date()
    desde = datetime.strptime(desde_str, "%Y-%m-%d").date() if desde_str else (hoy - timedelta(days=30))
    hasta = datetime.strptime(hasta_str, "%Y-%m-%d").date() if hasta_str else hoy

    service = ArticulosSinMovimientoService()
    report = service.run(desde, hasta, bodega_id=bodega_id, categoria_id=categoria_id)

    if fmt == "pdf":
        return export_pdf(report)
    if fmt == "xlsx":
        return export_xlsx(report)

    # HTML con filtros
    bodegas = Bodega.objects.filter(eliminado=False, activo=True).order_by("codigo")
    categorias = Categoria.objects.filter(eliminado=False).order_by("codigo")
    context = {
        "report": report,
        "bodegas": bodegas,
        "categorias": categorias,
        "desde": desde,
        "hasta": hasta,
        "bodega_id": bodega_id,
        "categoria_id": categoria_id,
    }
    return render(request, "reportes/articulos_sin_movimiento.html", context)


@login_required
def oc_atrasadas_por_proveedor(request: HttpRequest) -> HttpResponse:
    """
    En pantalla/PDF/XLSX de OC atrasadas por proveedor.
    Filtros: proveedor_id, bodega_id
    """
    fmt = request.GET.get("format", "html")
    proveedor_id = request.GET.get("proveedor_id")
    bodega_id = request.GET.get("bodega_id")

    service = OcAtrasadasPorProveedorService()
    report = service.run(proveedor_id=proveedor_id, bodega_id=bodega_id)

    if fmt == "pdf":
        return export_pdf(report)
    if fmt == "xlsx":
        return export_xlsx(report)

    proveedores = Proveedor.objects.filter(eliminado=False, activo=True).order_by("razon_social")
    bodegas = Bodega.objects.filter(eliminado=False, activo=True).order_by("codigo")
    context = {
        "report": report,
        "proveedores": proveedores,
        "bodegas": bodegas,
        "proveedor_id": proveedor_id,
        "bodega_id": bodega_id,
    }
    return render(request, "reportes/oc_atrasadas_por_proveedor.html", context)
