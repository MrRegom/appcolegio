from django.urls import path
from . import views

app_name = 'bodega'

urlpatterns = [
    # Menú principal de bodega
    path('', views.MenuBodegaView.as_view(), name='menu_bodega'),

    # Unidades de Medida (IMPORTANTE: Pertenecen a BODEGA, no a activos)
    path('unidades-medida/', views.UnidadMedidaListView.as_view(), name='lista_unidades'),
    path('unidades-medida/crear/', views.UnidadMedidaCreateView.as_view(), name='unidad_crear'),
    path('unidades-medida/<int:pk>/editar/', views.UnidadMedidaUpdateView.as_view(), name='unidad_editar'),
    path('unidades-medida/<int:pk>/eliminar/', views.UnidadMedidaDeleteView.as_view(), name='unidad_eliminar'),

    # Categorías
    path('categorias/', views.CategoriaListView.as_view(), name='categoria_lista'),
    path('categorias/crear/', views.CategoriaCreateView.as_view(), name='categoria_crear'),
    path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(), name='categoria_editar'),
    path('categorias/<int:pk>/eliminar/', views.CategoriaDeleteView.as_view(), name='categoria_eliminar'),

    # Artículos
    path('articulos/', views.ArticuloListView.as_view(), name='articulo_lista'),
    path('articulos/crear/', views.ArticuloCreateView.as_view(), name='articulo_crear'),
    path('articulos/<int:pk>/', views.ArticuloDetailView.as_view(), name='articulo_detalle'),
    path('articulos/<int:pk>/editar/', views.ArticuloUpdateView.as_view(), name='articulo_editar'),
    path('articulos/<int:pk>/eliminar/', views.ArticuloDeleteView.as_view(), name='articulo_eliminar'),

    # Movimientos
    path('movimientos/', views.MovimientoListView.as_view(), name='movimiento_lista'),
    path('movimientos/crear/', views.MovimientoCreateView.as_view(), name='movimiento_crear'),
    path('movimientos/<int:pk>/', views.MovimientoDetailView.as_view(), name='movimiento_detalle'),

    # Entregas de Artículos
    path('entregas/articulos/', views.EntregaArticuloListView.as_view(), name='entrega_articulo_lista'),
    path('entregas/articulos/crear/', views.EntregaArticuloCreateView.as_view(), name='entrega_articulo_crear'),
    path('entregas/articulos/<int:pk>/', views.EntregaArticuloDetailView.as_view(), name='entrega_articulo_detalle'),

    # Entregas de Bienes
    path('entregas/bienes/', views.EntregaBienListView.as_view(), name='entrega_bien_lista'),
    path('entregas/bienes/crear/', views.EntregaBienCreateView.as_view(), name='entrega_bien_crear'),
    path('entregas/bienes/<int:pk>/', views.EntregaBienDetailView.as_view(), name='entrega_bien_detalle'),

    # AJAX
    path('ajax/solicitud/<int:solicitud_id>/articulos/', views.obtener_articulos_solicitud, name='ajax_solicitud_articulos'),
    path('ajax/solicitud/<int:solicitud_id>/bienes/', views.obtener_bienes_solicitud, name='ajax_solicitud_bienes'),

    # ==================== MANTENEDORES ====================

    # Marcas
    path('mantenedores/marcas/', views.MarcaListView.as_view(), name='marca_lista'),
    path('mantenedores/marcas/crear/', views.MarcaCreateView.as_view(), name='marca_crear'),
    path('mantenedores/marcas/<int:pk>/editar/', views.MarcaUpdateView.as_view(), name='marca_editar'),
    path('mantenedores/marcas/<int:pk>/eliminar/', views.MarcaDeleteView.as_view(), name='marca_eliminar'),

    # Operaciones
    path('mantenedores/operaciones/', views.OperacionListView.as_view(), name='operacion_lista'),
    path('mantenedores/operaciones/crear/', views.OperacionCreateView.as_view(), name='operacion_crear'),
    path('mantenedores/operaciones/<int:pk>/editar/', views.OperacionUpdateView.as_view(), name='operacion_editar'),
    path('mantenedores/operaciones/<int:pk>/eliminar/', views.OperacionDeleteView.as_view(), name='operacion_eliminar'),

    # Tipos de Movimiento
    path('mantenedores/tipos-movimiento/', views.TipoMovimientoListView.as_view(), name='tipo_movimiento_lista'),
    path('mantenedores/tipos-movimiento/crear/', views.TipoMovimientoCreateView.as_view(), name='tipo_movimiento_crear'),
    path('mantenedores/tipos-movimiento/<int:pk>/editar/', views.TipoMovimientoUpdateView.as_view(), name='tipo_movimiento_editar'),
    path('mantenedores/tipos-movimiento/<int:pk>/eliminar/', views.TipoMovimientoDeleteView.as_view(), name='tipo_movimiento_eliminar'),
]
