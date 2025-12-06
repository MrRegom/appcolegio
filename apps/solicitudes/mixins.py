"""
Mixins personalizados para control de permisos del módulo de solicitudes.

Estos mixins extienden la funcionalidad de verificación de permisos
usando los permisos personalizados organizados por módulo.
"""

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from typing import List, Optional


class SolicitudPermissionMixin(PermissionRequiredMixin):
    """
    Mixin base para verificación de permisos en solicitudes.

    Extiende PermissionRequiredMixin para agregar lógica específica
    del módulo de solicitudes.
    """

    def handle_no_permission(self):
        """Maneja la falta de permisos mostrando mensaje al usuario."""
        if self.raise_exception or self.request.user.is_authenticated:
            messages.error(
                self.request,
                'No tiene permisos suficientes para realizar esta acción.'
            )
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('solicitudes:menu_solicitudes')


class GestionSolicitudesPermissionMixin(SolicitudPermissionMixin):
    """
    Mixin para vistas que requieren permisos de GESTIÓN.

    Verifica que el usuario tenga permisos de gestión completa
    del módulo de solicitudes.

    Permisos verificados:
    - gestionar_solicitudes
    - ver_todas_solicitudes
    """
    permission_required = 'solicitudes.gestionar_solicitudes'

    def has_permission(self):
        """Verifica si el usuario tiene permisos de gestión."""
        return (
            self.request.user.has_perm('solicitudes.gestionar_solicitudes') or
            self.request.user.has_perm('solicitudes.ver_todas_solicitudes')
        )


class AprobarSolicitudesPermissionMixin(SolicitudPermissionMixin):
    """
    Mixin para vistas que requieren permisos de APROBACIÓN.

    Verifica que el usuario pueda aprobar solicitudes.
    """
    permission_required = 'solicitudes.aprobar_solicitudes'


class RechazarSolicitudesPermissionMixin(SolicitudPermissionMixin):
    """
    Mixin para vistas que requieren permisos de RECHAZO.

    Verifica que el usuario pueda rechazar solicitudes.
    """
    permission_required = 'solicitudes.rechazar_solicitudes'


class DespacharSolicitudesPermissionMixin(SolicitudPermissionMixin):
    """
    Mixin para vistas que requieren permisos de DESPACHO.

    Verifica que el usuario pueda despachar solicitudes.
    """
    permission_required = 'solicitudes.despachar_solicitudes'


class CrearSolicitudArticulosPermissionMixin(SolicitudPermissionMixin):
    """
    Mixin para vistas de creación de solicitudes de ARTÍCULOS.

    Verifica que el usuario tenga permiso para crear solicitudes
    de artículos de bodega.
    """
    permission_required = 'solicitudes.crear_solicitud_articulos'


class CrearSolicitudBienesPermissionMixin(SolicitudPermissionMixin):
    """
    Mixin para vistas de creación de solicitudes de BIENES.

    Verifica que el usuario tenga permiso para crear solicitudes
    de bienes/activos de inventario.
    """
    permission_required = 'solicitudes.crear_solicitud_bienes'


class VerSolicitudesArticulosPermissionMixin(SolicitudPermissionMixin):
    """
    Mixin para vistas que muestran solicitudes de ARTÍCULOS.

    Verifica que el usuario pueda ver solicitudes de artículos.
    """
    permission_required = 'solicitudes.ver_solicitudes_articulos'


class VerSolicitudesBienesPermissionMixin(SolicitudPermissionMixin):
    """
    Mixin para vistas que muestran solicitudes de BIENES.

    Verifica que el usuario pueda ver solicitudes de bienes.
    """
    permission_required = 'solicitudes.ver_solicitudes_bienes'


class MisSolicitudesPermissionMixin(SolicitudPermissionMixin):
    """
    Mixin para vistas de MIS SOLICITUDES.

    Permite al usuario gestionar sus propias solicitudes.
    Verifica permisos específicos según la acción.
    """

    def has_permission(self):
        """
        Verifica permisos para gestionar solicitudes propias.

        Si el usuario tiene permisos de gestión completa, permite acceso.
        Si no, verifica permisos específicos de "mis solicitudes".
        """
        user = self.request.user

        # Administradores y gestores tienen acceso completo
        if user.has_perm('solicitudes.gestionar_solicitudes'):
            return True

        # Verificar permiso específico de ver mis solicitudes
        return user.has_perm('solicitudes.ver_mis_solicitudes')


class EditarMisSolicitudesPermissionMixin(SolicitudPermissionMixin):
    """
    Mixin para editar solicitudes propias.

    Verifica que:
    1. El usuario sea el solicitante O tenga permisos de gestión
    2. El usuario tenga permiso de editar sus solicitudes
    3. La solicitud esté en estado editable
    """

    def has_permission(self):
        """Verifica permisos para editar la solicitud."""
        user = self.request.user

        # Gestores pueden editar cualquier solicitud
        if user.has_perm('solicitudes.editar_cualquier_solicitud'):
            return True

        # Verificar si es el solicitante y tiene permiso
        solicitud = self.get_object()
        if solicitud.solicitante == user:
            return user.has_perm('solicitudes.editar_mis_solicitudes')

        return False

    def dispatch(self, request, *args, **kwargs):
        """Verifica que la solicitud pueda ser editada."""
        if not self.has_permission():
            messages.error(
                request,
                'No tiene permisos para editar esta solicitud.'
            )
            raise PermissionDenied

        # Verificar estado editable
        solicitud = self.get_object()
        if solicitud.estado.es_final:
            messages.warning(
                request,
                'No se puede editar una solicitud en estado final.'
            )
            return redirect('solicitudes:detalle_solicitud', pk=solicitud.pk)

        return super().dispatch(request, *args, **kwargs)


class EliminarMisSolicitudesPermissionMixin(SolicitudPermissionMixin):
    """
    Mixin para eliminar solicitudes propias.

    Verifica que:
    1. El usuario sea el solicitante O tenga permisos de gestión
    2. El usuario tenga permiso de eliminar sus solicitudes
    3. La solicitud esté en estado inicial (no procesada)
    """

    def has_permission(self):
        """Verifica permisos para eliminar la solicitud."""
        user = self.request.user

        # Gestores pueden eliminar cualquier solicitud
        if user.has_perm('solicitudes.eliminar_cualquier_solicitud'):
            return True

        # Verificar si es el solicitante y tiene permiso
        solicitud = self.get_object()
        if solicitud.solicitante == user:
            return user.has_perm('solicitudes.eliminar_mis_solicitudes')

        return False

    def dispatch(self, request, *args, **kwargs):
        """Verifica que la solicitud pueda ser eliminada."""
        if not self.has_permission():
            messages.error(
                request,
                'No tiene permisos para eliminar esta solicitud.'
            )
            raise PermissionDenied

        # Verificar estado eliminable (solo en estado inicial)
        solicitud = self.get_object()
        if not solicitud.estado.es_inicial:
            messages.warning(
                request,
                'Solo se pueden eliminar solicitudes en estado inicial.'
            )
            return redirect('solicitudes:detalle_solicitud', pk=solicitud.pk)

        return super().dispatch(request, *args, **kwargs)


class MultiplePermissionRequiredMixin(SolicitudPermissionMixin):
    """
    Mixin que permite verificar múltiples permisos.

    Puede requerir que el usuario tenga TODOS los permisos (require_all=True)
    o al menos UNO de los permisos (require_all=False).

    Example:
        class MiVista(MultiplePermissionRequiredMixin, ListView):
            permissions_required = [
                'solicitudes.crear_solicitud_articulos',
                'solicitudes.crear_solicitud_bienes',
            ]
            require_all = False  # Al menos uno de los permisos
    """
    permissions_required: List[str] = []
    require_all: bool = True  # True = AND, False = OR

    def has_permission(self):
        """Verifica los permisos según configuración."""
        if not self.permissions_required:
            return True

        perms = self.permissions_required
        user = self.request.user

        if self.require_all:
            # Requiere TODOS los permisos
            return all(user.has_perm(perm) for perm in perms)
        else:
            # Requiere AL MENOS UNO de los permisos
            return any(user.has_perm(perm) for perm in perms)


class OwnerOrPermissionRequiredMixin:
    """
    Mixin que permite acceso si el usuario es el dueño del objeto
    O tiene un permiso específico.

    Atributos:
        owner_field: Nombre del campo que identifica al dueño (default: 'solicitante')
        fallback_permission: Permiso alternativo que otorga acceso

    Example:
        class EditarSolicitudView(OwnerOrPermissionRequiredMixin, UpdateView):
            owner_field = 'solicitante'
            fallback_permission = 'solicitudes.editar_cualquier_solicitud'
    """
    owner_field: str = 'solicitante'
    fallback_permission: Optional[str] = None

    def dispatch(self, request, *args, **kwargs):
        """Verifica ownership o permiso antes de procesar."""
        obj = self.get_object()
        user = request.user

        # Verificar si es el dueño
        is_owner = getattr(obj, self.owner_field, None) == user

        # Verificar permiso alternativo
        has_fallback = (
            self.fallback_permission and
            user.has_perm(self.fallback_permission)
        )

        # Permitir acceso si es dueño O tiene permiso alternativo
        if not (is_owner or has_fallback):
            messages.error(
                request,
                'No tiene permisos para acceder a este recurso.'
            )
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
