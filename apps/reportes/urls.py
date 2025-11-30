from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    # Rutas específicas primero (antes de la ruta con parámetro)
    path('tipos/', views.lista_reportes, name='lista_reportes'),
    path('historial/', views.historial_reportes, name='historial_reportes'),
    path('inventario-actual/', views.reporte_inventario_actual, name='inventario_actual'),
    path('movimientos/', views.reporte_movimientos, name='movimientos'),
    # Vista de auditoría de actividades
    path('auditoria/', views.auditoria_actividades, name='auditoria_actividades'),
    # Nuevos reportes
    path('bodega/articulos-sin-movimiento/', views.articulos_sin_movimiento, name='articulos_sin_movimiento'),
    path('compras/oc-atrasadas-proveedor/', views.oc_atrasadas_por_proveedor, name='oc_atrasadas_por_proveedor'),
    # Ruta con parámetro de app (debe ir después de las rutas específicas)
    path('<str:app>/', views.dashboard_reportes, name='dashboard_app'),
    # Ruta sin parámetro (dashboard general)
    path('', views.dashboard_reportes, name='dashboard'),
]
