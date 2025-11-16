 ANÁLISIS DEL ESTADO ACTUAL

  ✅ Lo que YA existe:

  1. Gestión completa de Usuarios (CRUD)
  2. Gestión completa de Grupos/Roles (CRUD)
  3. Asignación de permisos a grupos
  4. Asignación de permisos directos a usuarios
  5. Sistema de auditoría con logs
  6. Menú principal de gestión (menu_usuarios)

  ❌ Lo que FALTA:

  1. Vista de listado de permisos del sistema
  2. Vista de detalle de permisos
  3. Gestión de permisos personalizados (crear/editar)
  4. Menú mejorado con accesos directos
  5. Enlaces en topbar más específicos

  ---
  🎯 PLAN DE IMPLEMENTACIÓN

  FASE 1: Vistas de Permisos

  1.1 Lista de Permisos
  - Vista para listar todos los permisos organizados por app/modelo
  - Filtros por app, modelo, tipo de permiso (add, change, delete, view)
  - Búsqueda por nombre o código de permiso
  - Muestra qué grupos y usuarios tienen cada permiso

  1.2 Detalle de Permiso
  - Información completa del permiso
  - Lista de grupos que tienen este permiso
  - Lista de usuarios que tienen este permiso (directo o por grupo)
  - Historial de asignaciones (si es necesario)

  1.3 Crear/Editar Permisos Personalizados
  - Formulario para crear permisos custom (ej: aprobar_solicitud, despachar_orden)
  - Selección de modelo al que aplica
  - Nombre y descripción del permiso

  ---
  FASE 2: Templates

  2.1 Lista de Permisos (lista_permisos.html)
  - Tabla con permisos agrupados por app
  - Filtros y búsqueda
  - Acciones: Ver detalle, Editar (si es custom)

  2.2 Detalle de Permiso (detalle_permiso.html)
  - Información del permiso
  - Tabs: Grupos, Usuarios, Configuración

  2.3 Formulario de Permiso (form_permiso.html)
  - Solo para permisos personalizados
  - Selección de content_type, codename, nombre

  ---
  FASE 3: URLs

  Añadir a accounts/urls.py:
  # Gestión de Permisos
  path('permisos/', views.lista_permisos, name='lista_permisos'),
  path('permisos/<int:pk>/', views.detalle_permiso, name='detalle_permiso'),
  path('permisos/crear/', views.crear_permiso, name='crear_permiso'),
  path('permisos/<int:pk>/editar/', views.editar_permiso, name='editar_permiso'),
  path('permisos/<int:pk>/eliminar/', views.eliminar_permiso, name='eliminar_permiso'),

  ---
  FASE 4: Mejorar Menú Principal

  Actualizar menu_usuarios.html con cards:
  - 👥 Gestión de Usuarios
  - 🛡️ Gestión de Roles/Grupos
  - 🔐 Gestión de Permisos
  - 📊 Auditoría y Logs

  ---
  FASE 5: Actualizar Topbar

  Modificar el menú "Gestión de Usuarios" para que sea un desplegable:

  📌 Administración
    └─ 🛡️ Gestión de Usuarios (desplegable)
        ├─ 👥 Usuarios
        ├─ 🔑 Roles/Grupos
        ├─ 🔐 Permisos
        └─ 📊 Logs de Auditoría

  ---
  FASE 6: Utilidades y Decoradores

  Crear utilidades para verificar permisos:
  - Decorador @required_permissions(['perm1', 'perm2'])
  - Mixin MultiplePermissionsRequiredMixin
  - Template tags para verificar permisos en templates

  ---
  📝 ESTRUCTURA DE ARCHIVOS A CREAR/MODIFICAR

  apps/accounts/
  ├── views.py                    # ✏️ Añadir vistas de permisos
  ├── urls.py                     # ✏️ Añadir rutas de permisos
  ├── forms.py                    # ✏️ Añadir PermissionForm
  ├── decorators.py               # 🆕 Crear decoradores custom
  └── templatetags/
      └── permissions_tags.py     # 🆕 Template tags personalizados

  templates/account/gestion_usuarios/
  ├── menu_usuarios.html          # ✏️ Mejorar con cards
  ├── lista_permisos.html         # 🆕 Nueva
  ├── detalle_permiso.html        # 🆕 Nueva
  ├── form_permiso.html           # 🆕 Nueva
  └── eliminar_permiso.html       # 🆕 Nueva

  templates/partials/
  └── topbar.html                 # ✏️ Actualizar menú

  ---
  ⚙️ CONFIGURACIÓN ADICIONAL

  Permisos personalizados en modelos

  Ejemplo en models.py:
  class Solicitud(models.Model):
      # ... campos ...

      class Meta:
          permissions = [
              ("aprobar_solicitud", "Puede aprobar solicitudes"),
              ("rechazar_solicitud", "Puede rechazar solicitudes"),
              ("despachar_solicitud", "Puede despachar solicitudes"),
          ]

  ---
  🚀 ORDEN DE IMPLEMENTACIÓN

  1. ✅ Exploración completada
  2. ⬜ Crear vistas de permisos (views.py)
  3. ⬜ Crear formularios (forms.py)
  4. ⬜ Actualizar URLs (urls.py)
  5. ⬜ Crear templates de permisos
  6. ⬜ Mejorar menú principal
  7. ⬜ Actualizar topbar
  8. ⬜ Crear decoradores y utilidades
  9. ⬜ Documentar sistema
  