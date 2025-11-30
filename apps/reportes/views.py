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
from apps.reportes.services.reporte import ReporteService
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


# ==================== NUEVOS REPORTES DINAMICOS ====================


@login_required
def seleccionar_reporte(request, modulo=None):
    """
    Vista unificada para seleccionar y generar reportes de forma dinamica.
    
    Flujo:
    1. Si no hay modulo: Muestra cards de modulos (Bodega, Compras, etc.)
    2. Si hay modulo pero no reporte: Muestra cards de reportes del modulo
    3. Si hay reporte seleccionado: Muestra filtros especificos
    4. Al hacer clic en "Crear Informe": Muestra tabla con datos
    
    SOLO ORQUESTA - Toda la logica de negocio esta en ReporteService.
    """
    # Si no hay modulo, mostrar seleccion de modulos
    if not modulo:
        modulos_disponibles = [
            {'codigo': 'auditoria', 'nombre': 'Auditoria', 'descripcion': 'Auditoria de actividades del sistema', 'icono': 'ri-time-line', 'tipo': 'auditoria'},
            {'codigo': 'bodega', 'nombre': 'Bodega', 'descripcion': 'Reportes del modulo de bodega e inventario', 'icono': 'ri-archive-line', 'tipo': 'reporte'},
            {'codigo': 'compras', 'nombre': 'Compras', 'descripcion': 'Reportes del modulo de compras y ordenes', 'icono': 'ri-shopping-cart-line', 'tipo': 'reporte'},
            {'codigo': 'solicitudes', 'nombre': 'Solicitudes', 'descripcion': 'Reportes del modulo de solicitudes', 'icono': 'ri-file-text-line', 'tipo': 'reporte'},
            {'codigo': 'activos', 'nombre': 'Activos', 'descripcion': 'Reportes del modulo de activos fijos', 'icono': 'ri-building-line', 'tipo': 'reporte'},
            {'codigo': 'bajas', 'nombre': 'Bajas', 'descripcion': 'Reportes del modulo de bajas de inventario', 'icono': 'ri-delete-bin-line', 'tipo': 'reporte'},
        ]
        context = {
            'titulo': 'Generar Reporte',
            'modulos_disponibles': modulos_disponibles,
            'mostrar_modulos': True,
        }
        return render(request, 'reportes/seleccionar_reporte.html', context)
    
    # Obtener reporte seleccionado desde GET
    reporte_codigo = request.GET.get('reporte', '').strip()
    crear_informe = request.GET.get('crear_informe', '').strip() == '1'
    
    # Obtener reportes disponibles desde Service Layer
    reportes_disponibles = ReporteService.obtener_reportes_por_modulo(modulo)
    
    # Si hay un reporte seleccionado, obtener su configuracion
    reporte_seleccionado = None
    filtros_config = {}
    opciones_filtros = {}
    
    if reporte_codigo:
        reporte_seleccionado = ReporteService.obtener_reporte_por_codigo(reporte_codigo)
        if reporte_seleccionado:
            filtros_config = ReporteService.obtener_filtros_para_reporte(reporte_codigo)
            
            # Obtener opciones para cada filtro
            for filtro_key, filtro_config in filtros_config.items():
                if filtro_config.get('tipo') == 'select' and filtro_config.get('opciones'):
                    opciones_filtros[filtro_key] = ReporteService.obtener_opciones_para_filtro(
                        filtro_config['opciones']
                    )
    
    # Si se solicito crear el informe, procesar y mostrar resultados
    report_data = None
    if crear_informe and reporte_seleccionado:
        # Obtener valores de filtros desde GET
        filtros_valores = {}
        for filtro_key in filtros_config.keys():
            valor = request.GET.get(filtro_key, '').strip()
            if valor:
                filtros_valores[filtro_key] = valor
        
        # Llamar al service correspondiente segun el tipo de reporte
        if reporte_codigo == 'articulos_sin_movimiento':
            desde_str = filtros_valores.get('desde')
            hasta_str = filtros_valores.get('hasta')
            bodega_id = filtros_valores.get('bodega_id')
            categoria_id = filtros_valores.get('categoria_id')
            
            hoy = timezone.now().date()
            desde = datetime.strptime(desde_str, "%Y-%m-%d").date() if desde_str else (hoy - timedelta(days=30))
            hasta = datetime.strptime(hasta_str, "%Y-%m-%d").date() if hasta_str else hoy
            
            service = ArticulosSinMovimientoService()
            report_data = service.run(desde, hasta, bodega_id=bodega_id, categoria_id=categoria_id)
            
        elif reporte_codigo == 'oc_atrasadas_por_proveedor':
            proveedor_id = filtros_valores.get('proveedor_id')
            bodega_id = filtros_valores.get('bodega_id')
            
            service = OcAtrasadasPorProveedorService()
            report_data = service.run(proveedor_id=proveedor_id, bodega_id=bodega_id)
    
    # Obtener opciones para filtros de tipo select
    bodegas = Bodega.objects.filter(eliminado=False, activo=True).order_by("codigo")
    categorias = Categoria.objects.filter(eliminado=False).order_by("codigo")
    proveedores = Proveedor.objects.filter(eliminado=False, activo=True).order_by("razon_social")
    
    # Nombre del modulo para mostrar
    nombres_modulos = {
        'bodega': 'Bodega',
        'compras': 'Compras',
        'solicitudes': 'Solicitudes',
        'activos': 'Activos',
        'bajas': 'Bajas',
    }
    nombre_modulo = nombres_modulos.get(modulo, modulo.capitalize())
    
    context = {
        'titulo': f'Reportes - {nombre_modulo}',
        'modulo': modulo,
        'nombre_modulo': nombre_modulo,
        'reportes_disponibles': reportes_disponibles,
        'reporte_seleccionado': reporte_seleccionado,
        'reporte_codigo': reporte_codigo,
        'filtros_config': filtros_config,
        'opciones_filtros': opciones_filtros,
        'bodegas': bodegas,
        'categorias': categorias,
        'proveedores': proveedores,
        'report': report_data,
        'crear_informe': crear_informe,
        'mostrar_modulos': False,
        # Valores actuales de filtros para mantener en el formulario
        'filtros_actuales': {
            'desde': request.GET.get('desde', ''),
            'hasta': request.GET.get('hasta', ''),
            'bodega_id': request.GET.get('bodega_id', ''),
            'categoria_id': request.GET.get('categoria_id', ''),
            'proveedor_id': request.GET.get('proveedor_id', ''),
        }
    }
    
    return render(request, 'reportes/seleccionar_reporte.html', context)


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


# ==================== VISTA DE AUDITORÍA DE ACTIVIDADES ====================


@login_required
def auditoria_actividades(request: HttpRequest) -> HttpResponse:
    """
    Vista dedicada para auditoría de actividades del sistema.

    SOLO ORQUESTA - Toda la lógica de negocio está en AuditoriaService.
    Sigue Clean Architecture: Views → solo orquestan, sin lógica pesada.

    Filtros disponibles:
    - tipo: Tipo de actividad (movimiento, entrega, solicitud, etc.)
    - usuario_id: ID del usuario
    - modulo: Módulo del sistema (bodega, compras, solicitudes, activos)
    - fecha_desde: Fecha inicial
    - fecha_hasta: Fecha final
    - buscar: Búsqueda por texto
    - page: Número de página para paginación
    """
    from .services.auditoria import AuditoriaService
    from django.contrib.auth import get_user_model
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

    User = get_user_model()

    # Obtener parámetros de filtro desde GET
    tipo = request.GET.get('tipo', '').strip() or None
    usuario_id = request.GET.get('usuario_id', '').strip()
    usuario_id = int(usuario_id) if usuario_id.isdigit() else None
    modulo = request.GET.get('modulo', '').strip() or None
    buscar = request.GET.get('buscar', '').strip() or None
    fecha_desde_str = request.GET.get('fecha_desde', '').strip()
    fecha_hasta_str = request.GET.get('fecha_hasta', '').strip()

    # Convertir fechas
    fecha_desde = None
    fecha_hasta = None
    if fecha_desde_str:
        try:
            fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d')
            fecha_desde = timezone.make_aware(fecha_desde)
        except ValueError:
            fecha_desde = None

    if fecha_hasta_str:
        try:
            fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d')
            fecha_hasta = timezone.make_aware(fecha_hasta)
            # Incluir todo el día
            fecha_hasta = fecha_hasta.replace(hour=23, minute=59, second=59)
        except ValueError:
            fecha_hasta = None

    # Si no hay fechas, usar últimos 30 días por defecto
    if not fecha_desde and not fecha_hasta:
        fecha_hasta = timezone.now()
        fecha_desde = fecha_hasta - timedelta(days=30)

    # Obtener actividades desde el Service Layer
    actividades = AuditoriaService.obtener_actividades(
        tipo=tipo,
        usuario_id=usuario_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        modulo=modulo,
        buscar=buscar,
        limite=500  # Límite alto para paginación
    )

    # Paginación
    paginator = Paginator(actividades, 50)  # 50 actividades por página
    page = request.GET.get('page', 1)

    try:
        actividades_paginadas = paginator.page(page)
    except PageNotAnInteger:
        actividades_paginadas = paginator.page(1)
    except EmptyPage:
        actividades_paginadas = paginator.page(paginator.num_pages)

    # Obtener estadísticas desde el Service Layer
    estadisticas = AuditoriaService.obtener_estadisticas_actividades()

    # Obtener lista de usuarios para el filtro
    usuarios = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username')[:100]

    # Contexto para el template
    context = {
        'titulo': 'Auditoría de Actividades',
        'actividades': actividades_paginadas,
        'estadisticas': estadisticas,
        'tipos_actividad': AuditoriaService.TIPOS_ACTIVIDAD,
        'modulos': {
            'bodega': 'Bodega',
            'compras': 'Compras',
            'solicitudes': 'Solicitudes',
            'activos': 'Activos',
        },
        'usuarios': usuarios,
        # Valores actuales de filtros para mantener en el formulario
        'filtros_actuales': {
            'tipo': tipo or '',
            'usuario_id': usuario_id or '',
            'modulo': modulo or '',
            'buscar': buscar or '',
            'fecha_desde': fecha_desde_str or '',
            'fecha_hasta': fecha_hasta_str or '',
        },
    }

    return render(request, 'reportes/auditoria_actividades.html', context)