from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    # Rutas especificas primero (antes de la ruta con parametro)
    path('tipos/', views.lista_reportes, name='lista_reportes'),
    path('historial/', views.historial_reportes, name='historial_reportes'),
    path('inventario-actual/', views.reporte_inventario_actual, name='inventario_actual'),
    path('movimientos/', views.reporte_movimientos, name='movimientos'),
    # Vista de auditoria de actividades
    path('auditoria/', views.auditoria_actividades, name='auditoria_actividades'),
    # Vista unificada de reportes dinamicos
    path('generar/<str:modulo>/', views.seleccionar_reporte, name='seleccionar_reporte_modulo'),
    path('generar/', views.seleccionar_reporte, name='seleccionar_reporte'),
    # Nuevos reportes (mantener para compatibilidad)
    path('bodega/articulos-sin-movimiento/', views.articulos_sin_movimiento, name='articulos_sin_movimiento'),
    path('compras/oc-atrasadas-proveedor/', views.oc_atrasadas_por_proveedor, name='oc_atrasadas_por_proveedor'),
    # Ruta con parametro de app (debe ir despues de las rutas especificas)
    path('<str:app>/', views.dashboard_reportes, name='dashboard_app'),
    # Ruta sin parametro (dashboard general)
    path('', views.dashboard_reportes, name='dashboard'),
]
