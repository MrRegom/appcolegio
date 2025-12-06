from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.db.models import Q, Count
from django.contrib.auth.models import User, Group, Permission
from django.db import transaction

from .forms import (
    UserCreateForm, UserUpdateForm, UserPasswordChangeForm,
    GroupForm, GroupPermissionsForm, UserGroupsForm, UserPermissionsForm,
    UserFilterForm, PermissionForm
)
from .models import AuthLogs, AuthLogAccion

# Importar utilidades centralizadas
from core.utils import registrar_log_auditoria


# ========== MENÚ PRINCIPAL ==========

class MenuAdministracionView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """
    Vista del menú principal de Administración.
    
    Incluye dos secciones:
    1. Administración de Usuarios (Usuarios, Roles/Grupos, Permisos)
    2. Organización (Ubicación, Talleres, Área, Departamentos)
    """
    template_name = 'account/menu_administracion.html'
    permission_required = 'auth.view_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Importar modelos de Organización
        from apps.activos.models import Ubicacion, Taller
        from apps.solicitudes.models import Area, Departamento

        # Estadísticas - Administración de Usuarios
        context['stats_usuarios'] = {
            'total_usuarios': User.objects.count(),
            'usuarios_activos': User.objects.filter(is_active=True).count(),
            'usuarios_staff': User.objects.filter(is_staff=True).count(),
            'total_grupos': Group.objects.count(),
            'total_permisos': Permission.objects.count(),
        }

        # Estadísticas - Organización
        context['stats_organizacion'] = {
            'total_ubicaciones': Ubicacion.objects.filter(eliminado=False).count(),
            'total_talleres': Taller.objects.filter(eliminado=False).count(),
            'total_areas': Area.objects.filter(eliminado=False).count(),
            'total_departamentos': Departamento.objects.filter(eliminado=False).count(),
        }

        # Permisos del usuario actual - Administración de Usuarios
        context['permisos_usuarios'] = {
            'puede_crear_usuarios': self.request.user.has_perm('auth.add_user'),
            'puede_editar_usuarios': self.request.user.has_perm('auth.change_user'),
            'puede_eliminar_usuarios': self.request.user.has_perm('auth.delete_user'),
            'puede_gestionar_grupos': self.request.user.has_perm('auth.change_group'),
            'puede_gestionar_permisos': self.request.user.has_perm('auth.view_permission'),
        }

        # Permisos del usuario actual - Organización
        context['permisos_organizacion'] = {
            'puede_gestionar_ubicacion': self.request.user.has_perm('activos.view_ubicacion'),
            'puede_gestionar_taller': self.request.user.has_perm('activos.view_taller'),
            'puede_gestionar_area': self.request.user.has_perm('solicitudes.view_area'),
            'puede_gestionar_departamento': self.request.user.has_perm('solicitudes.view_departamento'),
        }

        context['titulo'] = 'Administración'

        return context


# ========== GESTIÓN DE USUARIOS ==========

@login_required
@permission_required('auth.view_user', raise_exception=True)
def lista_usuarios(request):
    """Listar todos los usuarios con filtros"""
    form = UserFilterForm(request.GET or None)
    usuarios = User.objects.prefetch_related('groups').all()

    # Aplicar filtros
    if form.is_valid():
        buscar = form.cleaned_data.get('buscar')
        is_active = form.cleaned_data.get('is_active')
        is_staff = form.cleaned_data.get('is_staff')
        group = form.cleaned_data.get('group')

        if buscar:
            usuarios = usuarios.filter(
                Q(username__icontains=buscar) |
                Q(email__icontains=buscar) |
                Q(first_name__icontains=buscar) |
                Q(last_name__icontains=buscar)
            )

        if is_active != '':
            usuarios = usuarios.filter(is_active=is_active)

        if is_staff != '':
            usuarios = usuarios.filter(is_staff=is_staff)

        if group:
            usuarios = usuarios.filter(groups=group)

    # Permisos
    permisos = {
        'puede_crear': request.user.has_perm('auth.add_user'),
        'puede_editar': request.user.has_perm('auth.change_user'),
        'puede_eliminar': request.user.has_perm('auth.delete_user'),
        'puede_cambiar_password': request.user.has_perm('auth.change_user'),
    }

    context = {
        'titulo': 'Listado de Usuarios',
        'usuarios': usuarios,
        'form': form,
        'permisos': permisos,
    }

    return render(request, 'account/gestion_usuarios/lista_usuarios.html', context)


@login_required
@permission_required('auth.view_user', raise_exception=True)
def detalle_usuario(request, pk):
    """Ver detalle de un usuario"""
    usuario = get_object_or_404(User.objects.prefetch_related('groups', 'user_permissions'), pk=pk)

    # Permisos
    permisos = {
        'puede_editar': request.user.has_perm('auth.change_user'),
        'puede_eliminar': request.user.has_perm('auth.delete_user'),
        'puede_cambiar_password': request.user.has_perm('auth.change_user'),
    }

    context = {
        'titulo': f'Usuario: {usuario.username}',
        'usuario_detalle': usuario,
        'permisos': permisos,
    }

    return render(request, 'account/gestion_usuarios/detalle_usuario.html', context)


@login_required
@permission_required('auth.add_user', raise_exception=True)
@transaction.atomic
def crear_usuario(request):
    """Crear un nuevo usuario"""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            usuario = form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'CREAR',
                f'Usuario creado: {usuario.username}',
                request
            )

            messages.success(request, f'Usuario {usuario.username} creado exitosamente.')
            return redirect('accounts:detalle_usuario', pk=usuario.pk)
    else:
        form = UserCreateForm()

    context = {
        'titulo': 'Crear Usuario',
        'form': form,
        'action': 'Crear',
    }

    return render(request, 'account/gestion_usuarios/form_usuario.html', context)


@login_required
@permission_required('auth.change_user', raise_exception=True)
@transaction.atomic
def editar_usuario(request, pk):
    """Editar un usuario existente"""
    usuario = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=usuario)
        if form.is_valid():
            usuario = form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR',
                f'Usuario actualizado: {usuario.username}',
                request
            )

            messages.success(request, f'Usuario {usuario.username} actualizado exitosamente.')
            return redirect('accounts:detalle_usuario', pk=usuario.pk)
    else:
        form = UserUpdateForm(instance=usuario)

    context = {
        'titulo': f'Editar Usuario: {usuario.username}',
        'form': form,
        'action': 'Actualizar',
        'usuario_detalle': usuario,
    }

    return render(request, 'account/gestion_usuarios/form_usuario.html', context)


@login_required
@permission_required('auth.delete_user', raise_exception=True)
@transaction.atomic
def eliminar_usuario(request, pk):
    """Eliminar (desactivar) un usuario"""
    usuario = get_object_or_404(User, pk=pk)

    # No permitir eliminar superusuarios o el propio usuario
    if usuario.is_superuser:
        messages.error(request, 'No se puede eliminar un superusuario.')
        return redirect('accounts:lista_usuarios')

    if usuario == request.user:
        messages.error(request, 'No puedes eliminarte a ti mismo.')
        return redirect('accounts:lista_usuarios')

    if request.method == 'POST':
        username = usuario.username
        usuario.is_active = False
        usuario.save()

        # Registrar log
        registrar_log_auditoria(
            request.user,
            'ELIMINAR',
            f'Usuario desactivado: {username}',
            request
        )

        messages.success(request, f'Usuario {username} desactivado exitosamente.')
        return redirect('accounts:lista_usuarios')

    context = {
        'titulo': 'Eliminar Usuario',
        'usuario_detalle': usuario,
    }

    return render(request, 'account/gestion_usuarios/eliminar_usuario.html', context)


@login_required
@permission_required('auth.change_user', raise_exception=True)
@transaction.atomic
def cambiar_password_usuario(request, pk):
    """Cambiar contraseña de un usuario"""
    usuario = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserPasswordChangeForm(request.POST)
        if form.is_valid():
            usuario.set_password(form.cleaned_data['password1'])
            usuario.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR',
                f'Contraseña cambiada para usuario: {usuario.username}',
                request
            )

            messages.success(request, f'Contraseña de {usuario.username} actualizada exitosamente.')
            return redirect('accounts:detalle_usuario', pk=usuario.pk)
    else:
        form = UserPasswordChangeForm()

    context = {
        'titulo': f'Cambiar Contraseña: {usuario.username}',
        'form': form,
        'usuario_detalle': usuario,
    }

    return render(request, 'account/gestion_usuarios/cambiar_password.html', context)


# ========== GESTIÓN DE GRUPOS (ROLES) ==========

@login_required
@permission_required('auth.view_group', raise_exception=True)
def lista_grupos(request):
    """Listar todos los grupos/roles"""
    grupos = Group.objects.annotate(num_usuarios=Count('user')).all()

    # Permisos
    permisos = {
        'puede_crear': request.user.has_perm('auth.add_group'),
        'puede_editar': request.user.has_perm('auth.change_group'),
        'puede_eliminar': request.user.has_perm('auth.delete_group'),
    }

    context = {
        'titulo': 'Listado de Roles/Grupos',
        'grupos': grupos,
        'permisos': permisos,
    }

    return render(request, 'account/gestion_usuarios/lista_grupos.html', context)


@login_required
@permission_required('auth.view_group', raise_exception=True)
def detalle_grupo(request, pk):
    """Ver detalle de un grupo/rol"""
    grupo = get_object_or_404(
        Group.objects.prefetch_related('permissions', 'user_set'),
        pk=pk
    )

    # Permisos
    permisos = {
        'puede_editar': request.user.has_perm('auth.change_group'),
        'puede_eliminar': request.user.has_perm('auth.delete_group'),
    }

    context = {
        'titulo': f'Rol/Grupo: {grupo.name}',
        'grupo': grupo,
        'permisos': permisos,
    }

    return render(request, 'account/gestion_usuarios/detalle_grupo.html', context)


@login_required
@permission_required('auth.add_group', raise_exception=True)
@transaction.atomic
def crear_grupo(request):
    """Crear un nuevo grupo/rol"""
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            grupo = form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'CREAR',
                f'Grupo/Rol creado: {grupo.name}',
                request
            )

            messages.success(request, f'Rol {grupo.name} creado exitosamente.')
            return redirect('accounts:detalle_grupo', pk=grupo.pk)
    else:
        form = GroupForm()

    context = {
        'titulo': 'Crear Rol/Grupo',
        'form': form,
        'action': 'Crear',
    }

    return render(request, 'account/gestion_usuarios/form_grupo.html', context)


@login_required
@permission_required('auth.change_group', raise_exception=True)
@transaction.atomic
def editar_grupo(request, pk):
    """Editar un grupo/rol existente"""
    grupo = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        form = GroupForm(request.POST, instance=grupo)
        if form.is_valid():
            grupo = form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR',
                f'Grupo/Rol actualizado: {grupo.name}',
                request
            )

            messages.success(request, f'Rol {grupo.name} actualizado exitosamente.')
            return redirect('accounts:detalle_grupo', pk=grupo.pk)
    else:
        form = GroupForm(instance=grupo)

    context = {
        'titulo': f'Editar Rol: {grupo.name}',
        'form': form,
        'action': 'Actualizar',
        'grupo': grupo,
    }

    return render(request, 'account/gestion_usuarios/form_grupo.html', context)


@login_required
@permission_required('auth.delete_group', raise_exception=True)
@transaction.atomic
def eliminar_grupo(request, pk):
    """Eliminar un grupo/rol"""
    grupo = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        nombre = grupo.name
        grupo.delete()

        # Registrar log
        registrar_log_auditoria(
            request.user,
            'ELIMINAR',
            f'Grupo/Rol eliminado: {nombre}',
            request
        )

        messages.success(request, f'Rol {nombre} eliminado exitosamente.')
        return redirect('accounts:lista_grupos')

    context = {
        'titulo': 'Eliminar Rol/Grupo',
        'grupo': grupo,
    }

    return render(request, 'account/gestion_usuarios/eliminar_grupo.html', context)


# ========== ASIGNACIÓN DE PERMISOS Y GRUPOS ==========

@login_required
@permission_required('auth.change_group', raise_exception=True)
@transaction.atomic
def asignar_permisos_grupo(request, pk):
    """Asignar permisos a un grupo"""
    grupo = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        form = GroupPermissionsForm(request.POST, instance=grupo)
        if form.is_valid():
            form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR',
                f'Permisos actualizados para grupo: {grupo.name}',
                request
            )

            messages.success(request, f'Permisos del rol {grupo.name} actualizados exitosamente.')
            return redirect('accounts:detalle_grupo', pk=grupo.pk)
    else:
        form = GroupPermissionsForm(instance=grupo)

    # Importar CategoriaPermiso para permisos del módulo de solicitudes
    try:
        from apps.solicitudes.models import CategoriaPermiso
        # Obtener mapeo de permisos a categorías
        categorias_map = {
            cat.permiso_id: cat
            for cat in CategoriaPermiso.objects.select_related('permiso')
        }
    except ImportError:
        categorias_map = {}

    # Organizar permisos por app y categoría
    permisos_organizados = {}
    for permission in form.fields['permissions'].queryset:
        app_label = permission.content_type.app_label

        # Determinar la categoría
        if permission.id in categorias_map:
            # Si tiene categoría definida, usar la categoría
            categoria = categorias_map[permission.id]
            categoria_nombre = categoria.get_modulo_display()
            permission.categoria_obj = categoria  # Agregar para acceso en template
        else:
            # Si no tiene categoría, usar el nombre del modelo
            categoria_nombre = permission.content_type.model.title()
            permission.categoria_obj = None

        if app_label not in permisos_organizados:
            permisos_organizados[app_label] = {}

        if categoria_nombre not in permisos_organizados[app_label]:
            permisos_organizados[app_label][categoria_nombre] = []

        permisos_organizados[app_label][categoria_nombre].append(permission)

    context = {
        'titulo': f'Asignar Permisos: {grupo.name}',
        'form': form,
        'grupo': grupo,
        'permisos_organizados': permisos_organizados,
    }

    return render(request, 'account/gestion_usuarios/asignar_permisos_grupo.html', context)


@login_required
@permission_required('auth.change_user', raise_exception=True)
@transaction.atomic
def asignar_grupos_usuario(request, pk):
    """Asignar grupos/roles a un usuario"""
    usuario = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserGroupsForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR',
                f'Grupos actualizados para usuario: {usuario.username}',
                request
            )

            messages.success(request, f'Roles del usuario {usuario.username} actualizados exitosamente.')
            return redirect('accounts:detalle_usuario', pk=usuario.pk)
    else:
        form = UserGroupsForm(instance=usuario)

    context = {
        'titulo': f'Asignar Roles: {usuario.username}',
        'form': form,
        'usuario_detalle': usuario,
    }

    return render(request, 'account/gestion_usuarios/asignar_grupos_usuario.html', context)


@login_required
@permission_required('auth.change_user', raise_exception=True)
@transaction.atomic
def asignar_permisos_usuario(request, pk):
    """Asignar permisos específicos a un usuario"""
    usuario = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserPermissionsForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR',
                f'Permisos actualizados para usuario: {usuario.username}',
                request
            )

            messages.success(request, f'Permisos del usuario {usuario.username} actualizados exitosamente.')
            return redirect('accounts:detalle_usuario', pk=usuario.pk)
    else:
        form = UserPermissionsForm(instance=usuario)

    # Importar CategoriaPermiso para permisos del módulo de solicitudes
    try:
        from apps.solicitudes.models import CategoriaPermiso
        # Obtener mapeo de permisos a categorías
        categorias_map = {
            cat.permiso_id: cat
            for cat in CategoriaPermiso.objects.select_related('permiso')
        }
    except ImportError:
        categorias_map = {}

    # Organizar permisos por app y categoría
    permisos_organizados = {}
    for permission in form.fields['user_permissions'].queryset:
        app_label = permission.content_type.app_label

        # Determinar la categoría
        if permission.id in categorias_map:
            # Si tiene categoría definida, usar la categoría
            categoria = categorias_map[permission.id]
            categoria_nombre = categoria.get_modulo_display()
            permission.categoria_obj = categoria  # Agregar para acceso en template
        else:
            # Si no tiene categoría, usar el nombre del modelo
            categoria_nombre = permission.content_type.model.title()
            permission.categoria_obj = None

        if app_label not in permisos_organizados:
            permisos_organizados[app_label] = {}

        if categoria_nombre not in permisos_organizados[app_label]:
            permisos_organizados[app_label][categoria_nombre] = []

        permisos_organizados[app_label][categoria_nombre].append(permission)

    context = {
        'titulo': f'Asignar Permisos: {usuario.username}',
        'form': form,
        'usuario_detalle': usuario,
        'permisos_organizados': permisos_organizados,
    }

    return render(request, 'account/gestion_usuarios/asignar_permisos_usuario.html', context)


# ========== GESTIÓN DE PERMISOS ==========

@login_required
@permission_required('auth.view_permission', raise_exception=True)
def lista_permisos(request):
    """Listar permisos personalizados organizados por app y categoría"""
    # Obtener búsqueda y filtros
    buscar = request.GET.get('buscar', '')
    app_filter = request.GET.get('app', '')

    # Obtener solo permisos personalizados (excluir add_, change_, delete_, view_)
    permisos = Permission.objects.select_related('content_type').exclude(
        codename__startswith='add_'
    ).exclude(
        codename__startswith='change_'
    ).exclude(
        codename__startswith='delete_'
    ).exclude(
        codename__startswith='view_'
    )

    # Aplicar filtro de búsqueda
    if buscar:
        permisos = permisos.filter(
            Q(name__icontains=buscar) |
            Q(codename__icontains=buscar) |
            Q(content_type__model__icontains=buscar) |
            Q(content_type__app_label__icontains=buscar)
        )

    # Aplicar filtro por app
    if app_filter:
        permisos = permisos.filter(content_type__app_label=app_filter)

    # Importar CategoriaPermiso para permisos del módulo de solicitudes
    try:
        from apps.solicitudes.models import CategoriaPermiso
        # Obtener mapeo de permisos a categorías
        categorias_map = {
            cat.permiso_id: cat
            for cat in CategoriaPermiso.objects.select_related('permiso')
        }
    except ImportError:
        categorias_map = {}

    # Organizar permisos por app y categoría/modelo
    permisos_organizados = {}
    for permiso in permisos:
        app_label = permiso.content_type.app_label

        # Determinar la categoría
        if permiso.id in categorias_map:
            # Si tiene categoría definida, usar la categoría
            categoria = categorias_map[permiso.id]
            categoria_nombre = categoria.get_modulo_display()
            permiso.categoria_obj = categoria  # Agregar para acceso en template
        else:
            # Si no tiene categoría, usar el nombre del modelo
            categoria_nombre = permiso.content_type.model.title()
            permiso.categoria_obj = None

        if app_label not in permisos_organizados:
            permisos_organizados[app_label] = {}

        if categoria_nombre not in permisos_organizados[app_label]:
            permisos_organizados[app_label][categoria_nombre] = []

        permisos_organizados[app_label][categoria_nombre].append(permiso)

    # Obtener lista de apps para el filtro (solo apps con permisos personalizados)
    apps = Permission.objects.select_related('content_type').exclude(
        codename__startswith='add_'
    ).exclude(
        codename__startswith='change_'
    ).exclude(
        codename__startswith='delete_'
    ).exclude(
        codename__startswith='view_'
    ).values_list(
        'content_type__app_label', flat=True
    ).distinct().order_by('content_type__app_label')

    # Permisos del usuario
    permisos_usuario = {
        'puede_crear': request.user.has_perm('auth.add_permission'),
        'puede_editar': request.user.has_perm('auth.change_permission'),
        'puede_eliminar': request.user.has_perm('auth.delete_permission'),
    }

    context = {
        'titulo': 'Listado de Permisos',
        'permisos_organizados': permisos_organizados,
        'apps': apps,
        'buscar': buscar,
        'app_filter': app_filter,
        'permisos': permisos_usuario,
    }

    return render(request, 'account/gestion_usuarios/lista_permisos.html', context)


@login_required
@permission_required('auth.view_permission', raise_exception=True)
def detalle_permiso(request, pk):
    """Ver detalle de un permiso específico"""
    permiso = get_object_or_404(
        Permission.objects.select_related('content_type'),
        pk=pk
    )

    # Obtener grupos que tienen este permiso
    grupos_con_permiso = Group.objects.filter(permissions=permiso).annotate(
        num_usuarios=Count('user')
    )

    # Obtener usuarios que tienen este permiso directamente
    usuarios_con_permiso = User.objects.filter(user_permissions=permiso).select_related()

    # Permisos del usuario
    permisos_usuario = {
        'puede_editar': request.user.has_perm('auth.change_permission'),
        'puede_eliminar': request.user.has_perm('auth.delete_permission'),
    }

    context = {
        'titulo': f'Permiso: {permiso.name}',
        'permiso': permiso,
        'grupos_con_permiso': grupos_con_permiso,
        'usuarios_con_permiso': usuarios_con_permiso,
        'permisos': permisos_usuario,
    }

    return render(request, 'account/gestion_usuarios/detalle_permiso.html', context)


@login_required
@permission_required('auth.add_permission', raise_exception=True)
@transaction.atomic
def crear_permiso(request):
    """Crear un nuevo permiso personalizado"""
    if request.method == 'POST':
        form = PermissionForm(request.POST)
        if form.is_valid():
            permiso = form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'CREAR',
                f'Permiso personalizado creado: {permiso.codename}',
                request
            )

            messages.success(request, f'Permiso "{permiso.name}" creado exitosamente.')
            return redirect('accounts:detalle_permiso', pk=permiso.pk)
    else:
        form = PermissionForm()

    context = {
        'titulo': 'Crear Permiso Personalizado',
        'form': form,
        'action': 'Crear',
    }

    return render(request, 'account/gestion_usuarios/form_permiso.html', context)


@login_required
@permission_required('auth.change_permission', raise_exception=True)
@transaction.atomic
def editar_permiso(request, pk):
    """Editar un permiso personalizado"""
    permiso = get_object_or_404(Permission, pk=pk)

    # Verificar si es un permiso del sistema (auto-generado)
    # Los permisos del sistema tienen codenames que empiezan con add_, change_, delete_, view_
    es_permiso_sistema = permiso.codename.startswith(('add_', 'change_', 'delete_', 'view_'))

    if es_permiso_sistema:
        messages.warning(request, 'No se pueden editar los permisos del sistema.')
        return redirect('accounts:detalle_permiso', pk=permiso.pk)

    if request.method == 'POST':
        form = PermissionForm(request.POST, instance=permiso)
        if form.is_valid():
            permiso = form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR',
                f'Permiso personalizado actualizado: {permiso.codename}',
                request
            )

            messages.success(request, f'Permiso "{permiso.name}" actualizado exitosamente.')
            return redirect('accounts:detalle_permiso', pk=permiso.pk)
    else:
        form = PermissionForm(instance=permiso)

    context = {
        'titulo': f'Editar Permiso: {permiso.name}',
        'form': form,
        'action': 'Actualizar',
        'permiso': permiso,
    }

    return render(request, 'account/gestion_usuarios/form_permiso.html', context)


@login_required
@permission_required('auth.delete_permission', raise_exception=True)
@transaction.atomic
def eliminar_permiso(request, pk):
    """Eliminar un permiso personalizado"""
    permiso = get_object_or_404(Permission, pk=pk)

    # Verificar si es un permiso del sistema
    es_permiso_sistema = permiso.codename.startswith(('add_', 'change_', 'delete_', 'view_'))

    if es_permiso_sistema:
        messages.error(request, 'No se pueden eliminar los permisos del sistema.')
        return redirect('accounts:lista_permisos')

    if request.method == 'POST':
        nombre = permiso.name
        codename = permiso.codename
        permiso.delete()

        # Registrar log
        registrar_log_auditoria(
            request.user,
            'ELIMINAR',
            f'Permiso personalizado eliminado: {codename}',
            request
        )

        messages.success(request, f'Permiso "{nombre}" eliminado exitosamente.')
        return redirect('accounts:lista_permisos')

    context = {
        'titulo': 'Eliminar Permiso',
        'permiso': permiso,
    }

    return render(request, 'account/gestion_usuarios/eliminar_permiso.html', context)


# ========== GESTIÓN DE ORGANIZACIÓN ==========
# Vistas CRUD para Ubicación, Talleres, Área, Departamentos

from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q
from core.mixins import (
    BaseAuditedViewMixin, AtomicTransactionMixin, SoftDeleteMixin,
    PaginatedListMixin
)
from .forms import UbicacionForm, TallerForm, AreaForm, DepartamentoForm


# ==================== VISTAS DE UBICACIÓN ====================

class UbicacionListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar ubicaciones con paginación y filtros."""
    from apps.activos.models import Ubicacion
    model = Ubicacion
    template_name = 'account/organizacion/ubicacion/lista.html'
    context_object_name = 'ubicaciones'
    permission_required = 'activos.view_ubicacion'
    paginate_by = 25

    def get_queryset(self):
        """Retorna ubicaciones no eliminadas con búsqueda."""
        queryset = super().get_queryset().filter(eliminado=False)

        # Búsqueda por query string
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(codigo__icontains=query) |
                Q(nombre__icontains=query) |
                Q(descripcion__icontains=query)
            )

        return queryset.order_by('codigo')

    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Ubicaciones'
        context['query'] = self.request.GET.get('q', '')
        context['puede_crear'] = self.request.user.has_perm('activos.add_ubicacion')
        return context


class UbicacionCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """Vista para crear una nueva ubicación."""
    from apps.activos.models import Ubicacion
    model = Ubicacion
    form_class = UbicacionForm
    template_name = 'account/organizacion/ubicacion/form.html'
    permission_required = 'activos.add_ubicacion'
    success_url = reverse_lazy('accounts:ubicacion_lista')
    audit_action = 'CREAR'
    audit_description_template = 'Ubicación creada: {obj.codigo} - {obj.nombre}'
    success_message = 'Ubicación "{obj.nombre}" creada exitosamente.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Ubicación'
        context['action'] = 'Crear'
        return context


class UbicacionUpdateView(BaseAuditedViewMixin, AtomicTransactionMixin, UpdateView):
    """Vista para actualizar una ubicación existente."""
    from apps.activos.models import Ubicacion
    model = Ubicacion
    form_class = UbicacionForm
    template_name = 'account/organizacion/ubicacion/form.html'
    permission_required = 'activos.change_ubicacion'
    success_url = reverse_lazy('accounts:ubicacion_lista')
    audit_action = 'ACTUALIZAR'
    audit_description_template = 'Ubicación actualizada: {obj.codigo} - {obj.nombre}'
    success_message = 'Ubicación "{obj.nombre}" actualizada exitosamente.'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Ubicación: {self.object.nombre}'
        context['action'] = 'Actualizar'
        return context


class UbicacionDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """Vista para eliminar (soft delete) una ubicación."""
    from apps.activos.models import Ubicacion
    model = Ubicacion
    template_name = 'account/organizacion/ubicacion/eliminar.html'
    permission_required = 'activos.delete_ubicacion'
    success_url = reverse_lazy('accounts:ubicacion_lista')
    audit_action = 'ELIMINAR'
    audit_description_template = 'Ubicación eliminada: {obj.codigo} - {obj.nombre}'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Ubicación: {self.object.nombre}'
        return context


# ==================== VISTAS DE TALLER ====================

class TallerListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar talleres con paginación y filtros."""
    from apps.activos.models import Taller
    model = Taller
    template_name = 'account/organizacion/taller/lista.html'
    context_object_name = 'talleres'
    permission_required = 'activos.view_taller'
    paginate_by = 25

    def get_queryset(self):
        """Retorna talleres no eliminados con búsqueda."""
        queryset = super().get_queryset().filter(eliminado=False).select_related('responsable')

        # Búsqueda por query string
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(codigo__icontains=query) |
                Q(nombre__icontains=query) |
                Q(descripcion__icontains=query) |
                Q(ubicacion__icontains=query)
            )

        return queryset.order_by('codigo')

    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Talleres'
        context['query'] = self.request.GET.get('q', '')
        context['puede_crear'] = self.request.user.has_perm('activos.add_taller')
        return context


class TallerCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """Vista para crear un nuevo taller."""
    from apps.activos.models import Taller
    model = Taller
    form_class = TallerForm
    template_name = 'account/organizacion/taller/form.html'
    permission_required = 'activos.add_taller'
    success_url = reverse_lazy('accounts:taller_lista')
    audit_action = 'CREAR'
    audit_description_template = 'Taller creado: {obj.codigo} - {obj.nombre}'
    success_message = 'Taller "{obj.nombre}" creado exitosamente.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Taller'
        context['action'] = 'Crear'
        return context


class TallerUpdateView(BaseAuditedViewMixin, AtomicTransactionMixin, UpdateView):
    """Vista para actualizar un taller existente."""
    from apps.activos.models import Taller
    model = Taller
    form_class = TallerForm
    template_name = 'account/organizacion/taller/form.html'
    permission_required = 'activos.change_taller'
    success_url = reverse_lazy('accounts:taller_lista')
    audit_action = 'ACTUALIZAR'
    audit_description_template = 'Taller actualizado: {obj.codigo} - {obj.nombre}'
    success_message = 'Taller "{obj.nombre}" actualizado exitosamente.'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Taller: {self.object.nombre}'
        context['action'] = 'Actualizar'
        return context


class TallerDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """Vista para eliminar (soft delete) un taller."""
    from apps.activos.models import Taller
    model = Taller
    template_name = 'account/organizacion/taller/eliminar.html'
    permission_required = 'activos.delete_taller'
    success_url = reverse_lazy('accounts:taller_lista')
    audit_action = 'ELIMINAR'
    audit_description_template = 'Taller eliminado: {obj.codigo} - {obj.nombre}'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Taller: {self.object.nombre}'
        return context


# ==================== VISTAS DE ÁREA ====================

class AreaListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar áreas con paginación y filtros."""
    from apps.solicitudes.models import Area
    model = Area
    template_name = 'account/organizacion/area/lista.html'
    context_object_name = 'areas'
    permission_required = 'solicitudes.view_area'
    paginate_by = 25

    def get_queryset(self):
        """Retorna áreas no eliminadas con búsqueda."""
        queryset = super().get_queryset().filter(eliminado=False).select_related('departamento', 'responsable')

        # Búsqueda por query string
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(codigo__icontains=query) |
                Q(nombre__icontains=query) |
                Q(descripcion__icontains=query)
            )

        # Filtro por departamento
        departamento_id = self.request.GET.get('departamento', '')
        if departamento_id:
            queryset = queryset.filter(departamento_id=departamento_id)

        return queryset.order_by('codigo')

    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto."""
        from apps.solicitudes.models import Departamento
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Áreas'
        context['query'] = self.request.GET.get('q', '')
        context['departamento_id'] = self.request.GET.get('departamento', '')
        context['departamentos'] = Departamento.objects.filter(eliminado=False).order_by('codigo')
        context['puede_crear'] = self.request.user.has_perm('solicitudes.add_area')
        return context


class AreaCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """Vista para crear una nueva área."""
    from apps.solicitudes.models import Area
    model = Area
    form_class = AreaForm
    template_name = 'account/organizacion/area/form.html'
    permission_required = 'solicitudes.add_area'
    success_url = reverse_lazy('accounts:area_lista')
    audit_action = 'CREAR'
    audit_description_template = 'Área creada: {obj.codigo} - {obj.nombre}'
    success_message = 'Área "{obj.nombre}" creada exitosamente.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Área'
        context['action'] = 'Crear'
        return context


class AreaUpdateView(BaseAuditedViewMixin, AtomicTransactionMixin, UpdateView):
    """Vista para actualizar un área existente."""
    from apps.solicitudes.models import Area
    model = Area
    form_class = AreaForm
    template_name = 'account/organizacion/area/form.html'
    permission_required = 'solicitudes.change_area'
    success_url = reverse_lazy('accounts:area_lista')
    audit_action = 'ACTUALIZAR'
    audit_description_template = 'Área actualizada: {obj.codigo} - {obj.nombre}'
    success_message = 'Área "{obj.nombre}" actualizada exitosamente.'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Área: {self.object.nombre}'
        context['action'] = 'Actualizar'
        return context


class AreaDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """Vista para eliminar (soft delete) un área."""
    from apps.solicitudes.models import Area
    model = Area
    template_name = 'account/organizacion/area/eliminar.html'
    permission_required = 'solicitudes.delete_area'
    success_url = reverse_lazy('accounts:area_lista')
    audit_action = 'ELIMINAR'
    audit_description_template = 'Área eliminada: {obj.codigo} - {obj.nombre}'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Área: {self.object.nombre}'
        # Verificar si tiene relaciones
        context['tiene_solicitudes'] = hasattr(self.object, 'solicitudes') and self.object.solicitudes.filter(eliminado=False).exists()
        return context


# ==================== VISTAS DE DEPARTAMENTO ====================

class DepartamentoListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar departamentos con paginación y filtros."""
    from apps.solicitudes.models import Departamento
    model = Departamento
    template_name = 'account/organizacion/departamento/lista.html'
    context_object_name = 'departamentos'
    permission_required = 'solicitudes.view_departamento'
    paginate_by = 25

    def get_queryset(self):
        """Retorna departamentos no eliminados con búsqueda."""
        queryset = super().get_queryset().filter(eliminado=False).select_related('responsable')

        # Búsqueda por query string
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(codigo__icontains=query) |
                Q(nombre__icontains=query) |
                Q(descripcion__icontains=query)
            )

        return queryset.order_by('codigo')

    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Departamentos'
        context['query'] = self.request.GET.get('q', '')
        context['puede_crear'] = self.request.user.has_perm('solicitudes.add_departamento')
        return context


class DepartamentoCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """Vista para crear un nuevo departamento."""
    from apps.solicitudes.models import Departamento
    model = Departamento
    form_class = DepartamentoForm
    template_name = 'account/organizacion/departamento/form.html'
    permission_required = 'solicitudes.add_departamento'
    success_url = reverse_lazy('accounts:departamento_lista')
    audit_action = 'CREAR'
    audit_description_template = 'Departamento creado: {obj.codigo} - {obj.nombre}'
    success_message = 'Departamento "{obj.nombre}" creado exitosamente.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Departamento'
        context['action'] = 'Crear'
        return context


class DepartamentoUpdateView(BaseAuditedViewMixin, AtomicTransactionMixin, UpdateView):
    """Vista para actualizar un departamento existente."""
    from apps.solicitudes.models import Departamento
    model = Departamento
    form_class = DepartamentoForm
    template_name = 'account/organizacion/departamento/form.html'
    permission_required = 'solicitudes.change_departamento'
    success_url = reverse_lazy('accounts:departamento_lista')
    audit_action = 'ACTUALIZAR'
    audit_description_template = 'Departamento actualizado: {obj.codigo} - {obj.nombre}'
    success_message = 'Departamento "{obj.nombre}" actualizado exitosamente.'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Departamento: {self.object.nombre}'
        context['action'] = 'Actualizar'
        return context


class DepartamentoDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """Vista para eliminar (soft delete) un departamento."""
    from apps.solicitudes.models import Departamento
    model = Departamento
    template_name = 'account/organizacion/departamento/eliminar.html'
    permission_required = 'solicitudes.delete_departamento'
    success_url = reverse_lazy('accounts:departamento_lista')
    audit_action = 'ELIMINAR'
    audit_description_template = 'Departamento eliminado: {obj.codigo} - {obj.nombre}'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Departamento: {self.object.nombre}'
        # Verificar si tiene áreas relacionadas
        context['tiene_areas'] = self.object.areas.filter(eliminado=False).exists()
        return context
