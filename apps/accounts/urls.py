from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Menú principal
    path('', views.MenuAdministracionView.as_view(), name='menu_administracion'),
    # Alias para compatibilidad
    path('menu-usuarios/', views.MenuAdministracionView.as_view(), name='menu_usuarios'),

    # Gestión de Usuarios
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/<int:pk>/', views.detalle_usuario, name='detalle_usuario'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:pk>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:pk>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('usuarios/<int:pk>/cambiar-password/', views.cambiar_password_usuario, name='cambiar_password_usuario'),

    # Asignación de roles y permisos a usuarios
    path('usuarios/<int:pk>/asignar-grupos/', views.asignar_grupos_usuario, name='asignar_grupos_usuario'),
    path('usuarios/<int:pk>/asignar-permisos/', views.asignar_permisos_usuario, name='asignar_permisos_usuario'),

    # Gestión de Grupos/Roles
    path('grupos/', views.lista_grupos, name='lista_grupos'),
    path('grupos/<int:pk>/', views.detalle_grupo, name='detalle_grupo'),
    path('grupos/crear/', views.crear_grupo, name='crear_grupo'),
    path('grupos/<int:pk>/editar/', views.editar_grupo, name='editar_grupo'),
    path('grupos/<int:pk>/eliminar/', views.eliminar_grupo, name='eliminar_grupo'),

    # Asignación de permisos a grupos
    path('grupos/<int:pk>/asignar-permisos/', views.asignar_permisos_grupo, name='asignar_permisos_grupo'),

    # Gestión de Permisos
    path('permisos/', views.lista_permisos, name='lista_permisos'),
    path('permisos/<int:pk>/', views.detalle_permiso, name='detalle_permiso'),
    path('permisos/crear/', views.crear_permiso, name='crear_permiso'),
    path('permisos/<int:pk>/editar/', views.editar_permiso, name='editar_permiso'),
    path('permisos/<int:pk>/eliminar/', views.eliminar_permiso, name='eliminar_permiso'),

    # ========== GESTIÓN DE ORGANIZACIÓN ==========
    
    # Ubicaciones
    path('organizacion/ubicaciones/', views.UbicacionListView.as_view(), name='ubicacion_lista'),
    path('organizacion/ubicaciones/crear/', views.UbicacionCreateView.as_view(), name='ubicacion_crear'),
    path('organizacion/ubicaciones/<int:pk>/editar/', views.UbicacionUpdateView.as_view(), name='ubicacion_editar'),
    path('organizacion/ubicaciones/<int:pk>/eliminar/', views.UbicacionDeleteView.as_view(), name='ubicacion_eliminar'),

    # Talleres
    path('organizacion/talleres/', views.TallerListView.as_view(), name='taller_lista'),
    path('organizacion/talleres/crear/', views.TallerCreateView.as_view(), name='taller_crear'),
    path('organizacion/talleres/<int:pk>/editar/', views.TallerUpdateView.as_view(), name='taller_editar'),
    path('organizacion/talleres/<int:pk>/eliminar/', views.TallerDeleteView.as_view(), name='taller_eliminar'),

    # Áreas
    path('organizacion/areas/', views.AreaListView.as_view(), name='area_lista'),
    path('organizacion/areas/crear/', views.AreaCreateView.as_view(), name='area_crear'),
    path('organizacion/areas/<int:pk>/editar/', views.AreaUpdateView.as_view(), name='area_editar'),
    path('organizacion/areas/<int:pk>/eliminar/', views.AreaDeleteView.as_view(), name='area_eliminar'),

    # Departamentos
    path('organizacion/departamentos/', views.DepartamentoListView.as_view(), name='departamento_lista'),
    path('organizacion/departamentos/crear/', views.DepartamentoCreateView.as_view(), name='departamento_crear'),
    path('organizacion/departamentos/<int:pk>/editar/', views.DepartamentoUpdateView.as_view(), name='departamento_editar'),
    path('organizacion/departamentos/<int:pk>/eliminar/', views.DepartamentoDeleteView.as_view(), name='departamento_eliminar'),
]
