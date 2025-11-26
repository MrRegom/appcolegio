from django.urls import path
from . import views

app_name = 'solicitudes'

urlpatterns = [
    # Menú principal de solicitudes
    path('', views.MenuSolicitudesView.as_view(), name='menu_solicitudes'),

    # ==================== LISTADOS ====================
    # Gestión de Solicitudes: muestra TODAS las solicitudes
    path('gestion/', views.SolicitudListView.as_view(), name='lista_solicitudes'),
    # Mis Solicitudes: muestra solo las solicitudes del usuario actual
    path('mis-solicitudes/', views.MisSolicitudesListView.as_view(), name='mis_solicitudes'),

    # ==================== DETALLE Y EDICIÓN ====================
    path('<int:pk>/', views.SolicitudDetailView.as_view(), name='detalle_solicitud'),
    path('<int:pk>/editar/', views.SolicitudUpdateView.as_view(), name='editar_solicitud'),
    path('<int:pk>/eliminar/', views.SolicitudDeleteView.as_view(), name='eliminar_solicitud'),

    # ==================== FLUJO DE APROBACIÓN Y DESPACHO ====================
    path('<int:pk>/aprobar/', views.SolicitudAprobarView.as_view(), name='aprobar_solicitud'),
    path('<int:pk>/rechazar/', views.SolicitudRechazarView.as_view(), name='rechazar_solicitud'),
    path('<int:pk>/despachar/', views.SolicitudDespacharView.as_view(), name='despachar_solicitud'),

    # ==================== CREACIÓN DE SOLICITUDES ====================
    # Solicitudes de Bienes (tipo=ACTIVO)
    path('bienes/', views.SolicitudActivoListView.as_view(), name='lista_solicitudes_bienes'),
    path('bienes/crear/', views.SolicitudActivoCreateView.as_view(), name='crear_solicitud_bienes'),
    path('bienes/<int:pk>/editar/', views.SolicitudActivoUpdateView.as_view(), name='editar_solicitud_bienes'),

    # Solicitudes de Artículos (tipo=ARTICULO)
    path('articulos/', views.SolicitudArticuloListView.as_view(), name='lista_solicitudes_articulos'),
    path('articulos/crear/', views.SolicitudArticuloCreateView.as_view(), name='crear_solicitud_articulos'),
    path('articulos/<int:pk>/editar/', views.SolicitudArticuloUpdateView.as_view(), name='editar_solicitud_articulos'),

    # ==================== MANTENEDORES: TIPOS DE SOLICITUD ====================
    path('tipos/', views.TipoSolicitudListView.as_view(), name='tipo_solicitud_lista'),
    path('tipos/crear/', views.TipoSolicitudCreateView.as_view(), name='tipo_solicitud_crear'),
    path('tipos/<int:pk>/editar/', views.TipoSolicitudUpdateView.as_view(), name='tipo_solicitud_editar'),
    path('tipos/<int:pk>/eliminar/', views.TipoSolicitudDeleteView.as_view(), name='tipo_solicitud_eliminar'),

    # ==================== MANTENEDORES: ESTADOS DE SOLICITUD ====================
    path('estados/', views.EstadoSolicitudListView.as_view(), name='estado_solicitud_lista'),
    path('estados/crear/', views.EstadoSolicitudCreateView.as_view(), name='estado_solicitud_crear'),
    path('estados/<int:pk>/editar/', views.EstadoSolicitudUpdateView.as_view(), name='estado_solicitud_editar'),
    path('estados/<int:pk>/eliminar/', views.EstadoSolicitudDeleteView.as_view(), name='estado_solicitud_eliminar'),
]
