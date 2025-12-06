"""
Class-Based Views para el módulo de solicitudes.

Este archivo implementa todas las vistas usando CBVs siguiendo SOLID y DRY:
- Reutilización de mixins de core.mixins
- Separación de responsabilidades (Repository Pattern + Service Layer)
- Código limpio y mantenible
- Type hints completos
- Auditoría automática
- Workflow de aprobación y despacho
"""
from typing import Any
from django.db.models import QuerySet, Q
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, View
)
from core.mixins import (
    BaseAuditedViewMixin, AtomicTransactionMixin, SoftDeleteMixin,
    PaginatedListMixin, FilteredListMixin
)
from core.utils import registrar_log_auditoria
from .mixins import (
    GestionSolicitudesPermissionMixin,
    AprobarSolicitudesPermissionMixin,
    RechazarSolicitudesPermissionMixin,
    DespacharSolicitudesPermissionMixin,
    CrearSolicitudArticulosPermissionMixin,
    CrearSolicitudBienesPermissionMixin,
    VerSolicitudesArticulosPermissionMixin,
    VerSolicitudesBienesPermissionMixin,
    MisSolicitudesPermissionMixin,
    EditarMisSolicitudesPermissionMixin,
    EliminarMisSolicitudesPermissionMixin,
)
from .models import Solicitud, TipoSolicitud, EstadoSolicitud, DetalleSolicitud, HistorialSolicitud
from .forms import (
    SolicitudForm, DetalleSolicitudArticuloFormSet, DetalleSolicitudActivoFormSet,
    AprobarSolicitudForm, DespacharSolicitudForm, RechazarSolicitudForm,
    FiltroSolicitudesForm, TipoSolicitudForm, EstadoSolicitudForm
)
from .repositories import (
    TipoSolicitudRepository, EstadoSolicitudRepository, SolicitudRepository,
    DetalleSolicitudRepository, HistorialSolicitudRepository
)
from .services import SolicitudService, DetalleSolicitudService
from decimal import Decimal


# ==================== VISTA MENÚ PRINCIPAL ====================

class MenuSolicitudesView(BaseAuditedViewMixin, TemplateView):
    """
    Vista del menú principal del módulo de solicitudes.

    Muestra estadísticas y accesos rápidos basados en permisos del usuario.
    Permisos: solicitudes.view_solicitud
    Utiliza: Repositories para acceso a datos optimizado
    """
    template_name = 'solicitudes/menu_solicitudes.html'
    permission_required = 'solicitudes.view_solicitud'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega estadísticas y permisos al contexto usando repositories."""
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Inicializar repositories
        solicitud_repo = SolicitudRepository()
        estado_repo = EstadoSolicitudRepository()
        tipo_repo = TipoSolicitudRepository()

        # Estadísticas del módulo usando repositories
        estado_pendiente = estado_repo.get_by_codigo('PENDIENTE')
        pendientes_count = 0
        if estado_pendiente:
            pendientes_count = solicitud_repo.filter_by_estado(estado_pendiente).count()

        context['stats'] = {
            'total_solicitudes': solicitud_repo.get_all().count(),
            'mis_solicitudes': solicitud_repo.filter_by_solicitante(user).count(),
            'solicitudes_activos': solicitud_repo.filter_by_tipo_choice('ACTIVO').count(),
            'solicitudes_articulos': solicitud_repo.filter_by_tipo_choice('ARTICULO').count(),
            'pendientes': pendientes_count,
            # Estadísticas de mantenedores
            'total_tipos_solicitud': tipo_repo.get_all().count(),
            'total_estados_solicitud': estado_repo.get_all().count(),
        }

        # Permisos del usuario (usando nuevos permisos personalizados)
        context['permisos'] = {
            # Permisos de gestión
            'puede_gestionar': user.has_perm('solicitudes.gestionar_solicitudes'),
            'puede_aprobar': user.has_perm('solicitudes.aprobar_solicitudes'),
            'puede_rechazar': user.has_perm('solicitudes.rechazar_solicitudes'),
            'puede_despachar': user.has_perm('solicitudes.despachar_solicitudes'),
            'puede_ver_todas': user.has_perm('solicitudes.ver_todas_solicitudes'),

            # Permisos de solicitud de artículos
            'puede_crear_articulos': user.has_perm('solicitudes.crear_solicitud_articulos'),
            'puede_ver_solicitudes_articulos': user.has_perm('solicitudes.ver_solicitudes_articulos'),

            # Permisos de solicitud de bienes
            'puede_crear_bienes': user.has_perm('solicitudes.crear_solicitud_bienes'),
            'puede_ver_solicitudes_bienes': user.has_perm('solicitudes.ver_solicitudes_bienes'),

            # Permisos de mis solicitudes
            'puede_ver_mis_solicitudes': user.has_perm('solicitudes.ver_mis_solicitudes'),
            'puede_editar_mis_solicitudes': user.has_perm('solicitudes.editar_mis_solicitudes'),
            'puede_eliminar_mis_solicitudes': user.has_perm('solicitudes.eliminar_mis_solicitudes'),

            # Permisos para mantenedores
            'puede_gestionar_mantenedores': (
                user.has_perm('solicitudes.view_tiposolicitud') or
                user.has_perm('solicitudes.change_tiposolicitud') or
                user.has_perm('solicitudes.view_estadosolicitud') or
                user.has_perm('solicitudes.change_estadosolicitud')
            ),
        }

        context['titulo'] = 'Módulo de Solicitudes'
        return context


# ==================== VISTAS DE SOLICITUDES GENERALES ====================

class SolicitudListView(GestionSolicitudesPermissionMixin, BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para listar todas las solicitudes con filtros (GESTIÓN).

    Permisos: solicitudes.ver_todas_solicitudes o solicitudes.gestionar_solicitudes
    Filtros: Estado, tipo, fechas, búsqueda
    """
    model = Solicitud
    template_name = 'solicitudes/lista_solicitudes.html'
    context_object_name = 'solicitudes'
    paginate_by = 25
    filter_form_class = FiltroSolicitudesForm

    def get_queryset(self) -> QuerySet:
        """Retorna solicitudes con relaciones optimizadas y filtros."""
        queryset = super().get_queryset().select_related(
            'tipo_solicitud', 'estado', 'solicitante', 'bodega_origen'
        )

        # Aplicar filtros del formulario
        form = self.filter_form_class(self.request.GET)
        if form.is_valid():
            data = form.cleaned_data

            if data.get('estado'):
                queryset = queryset.filter(estado=data['estado'])

            if data.get('tipo'):
                queryset = queryset.filter(tipo_solicitud=data['tipo'])

            if data.get('fecha_desde'):
                queryset = queryset.filter(fecha_solicitud__gte=data['fecha_desde'])

            if data.get('fecha_hasta'):
                queryset = queryset.filter(fecha_solicitud__lte=data['fecha_hasta'])

            if data.get('buscar'):
                q = data['buscar']
                queryset = queryset.filter(
                    Q(numero__icontains=q) |
                    Q(solicitante__username__icontains=q) |
                    Q(area__nombre__icontains=q) |
                    Q(departamento__nombre__icontains=q)
                )

        return queryset.order_by('-fecha_solicitud')

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Solicitudes'
        context['form'] = self.filter_form_class(self.request.GET)
        return context


class SolicitudDetailView(BaseAuditedViewMixin, DetailView):
    """
    Vista para ver el detalle de una solicitud.

    Permisos: solicitudes.view_solicitud
    """
    model = Solicitud
    template_name = 'solicitudes/detalle_solicitud.html'
    context_object_name = 'solicitud'
    permission_required = 'solicitudes.view_solicitud'

    def get_queryset(self) -> QuerySet:
        """Optimiza consultas con select_related."""
        return super().get_queryset().select_related(
            'tipo_solicitud', 'estado', 'solicitante', 'aprobador',
            'despachador', 'bodega_origen'
        )

    def get_context_data(self, **kwargs) -> dict:
        """Agrega detalles y historial al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Solicitud {self.object.numero}'

        # Detalles de la solicitud
        # No usamos select_related porque DetalleSolicitud puede tener articulo O activo
        # Django hará queries lazy loading según corresponda
        context['detalles'] = self.object.detalles.filter(eliminado=False).select_related(
            'articulo',  # Para artículos de bodega
            'articulo__categoria',
            'activo',  # Para activos/bienes de inventario
            'activo__categoria'
        ).order_by('id')

        # Historial de cambios
        context['historial'] = self.object.historial.select_related(
            'estado_anterior', 'estado_nuevo', 'usuario'
        )

        return context

    def get_template_names(self):
        # Si la petición es AJAX o se solicita modal, devolver plantilla parcial
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('modal') == '1':
            return ['solicitudes/partials/modal_detalle.html']
        return [self.template_name]


class MisSolicitudesListView(MisSolicitudesPermissionMixin, BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para ver las solicitudes del usuario actual (MIS SOLICITUDES).

    Permisos: solicitudes.ver_mis_solicitudes
    """
    model = Solicitud
    template_name = 'solicitudes/mis_solicitudes.html'
    context_object_name = 'solicitudes'
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        """Retorna solo las solicitudes del usuario actual."""
        return super().get_queryset().filter(
            solicitante=self.request.user
        ).select_related(
            'tipo_solicitud', 'estado', 'bodega_origen'
        ).order_by('-fecha_solicitud')

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Mis Solicitudes'
        return context


class SolicitudCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """
    Vista para crear una nueva solicitud.

    Permisos: solicitudes.add_solicitud
    Auditoría: Registra acción CREAR automáticamente
    Transacción atómica: Garantiza que solicitud y detalles se creen correctamente
    """
    model = Solicitud
    form_class = SolicitudForm
    template_name = 'solicitudes/form_solicitud.html'
    permission_required = 'solicitudes.add_solicitud'

    # Configuración de auditoría
    audit_action = 'CREAR'
    audit_description_template = 'Creó solicitud {obj.numero}'

    # Mensaje de éxito
    success_message = 'Solicitud {obj.numero} creada exitosamente.'

    def get_success_url(self) -> str:
        """Redirige al detalle de la solicitud creada."""
        return reverse_lazy('solicitudes:detalle_solicitud', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        """Agrega formset y datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Solicitud'
        context['action'] = 'Crear'

        # Las vistas hijas deben sobrescribir esto con el formset correcto
        if self.request.POST:
            context['formset'] = DetalleSolicitudActivoFormSet(self.request.POST)
        else:
            context['formset'] = DetalleSolicitudActivoFormSet()

        return context

    def form_valid(self, form):
        """Procesa el formulario válido usando SolicitudService."""
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            solicitud_service = SolicitudService()

            try:
                # Crear solicitud usando service
                self.object = solicitud_service.crear_solicitud(
                    tipo_solicitud=form.cleaned_data['tipo_solicitud'],
                    solicitante=self.request.user,
                    fecha_requerida=form.cleaned_data['fecha_requerida'],
                    motivo=form.cleaned_data['motivo'],
                    titulo_actividad=form.cleaned_data.get('titulo_actividad', ''),
                    objetivo_actividad=form.cleaned_data.get('objetivo_actividad', ''),
                    tipo_choice=form.cleaned_data.get('tipo', 'ARTICULO'),
                    bodega_origen=form.cleaned_data.get('bodega_origen'),
                    departamento=form.cleaned_data.get('departamento'),
                    area=form.cleaned_data.get('area'),
                    equipo=form.cleaned_data.get('equipo'),
                    observaciones=form.cleaned_data.get('observaciones', '')
                )

                # Guardar los detalles
                formset.instance = self.object
                formset.save()

                # Mensaje de éxito y log de auditoría
                messages.success(self.request, self.get_success_message(self.object))
                self.log_action(self.object, self.request)

                return redirect(self.get_success_url())

            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field if field != '__all__' else None, error)
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)


class SolicitudUpdateView(EditarMisSolicitudesPermissionMixin, BaseAuditedViewMixin, AtomicTransactionMixin, UpdateView):
    """
    Vista para editar una solicitud existente (MIS SOLICITUDES).

    Permisos: solicitudes.editar_mis_solicitudes (si es el solicitante)
             o solicitudes.editar_cualquier_solicitud (si es gestor)
    Auditoría: Registra acción EDITAR automáticamente
    Transacción atómica: Garantiza consistencia de datos
    """
    model = Solicitud
    form_class = SolicitudForm
    template_name = 'solicitudes/form_solicitud.html'

    # Configuración de auditoría
    audit_action = 'EDITAR'
    audit_description_template = 'Editó solicitud {obj.numero}'

    # Mensaje de éxito
    success_message = 'Solicitud {obj.numero} actualizada exitosamente.'

    def get_success_url(self) -> str:
        """Redirige al detalle de la solicitud editada."""
        return reverse_lazy('solicitudes:detalle_solicitud', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        """Agrega formset y datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Solicitud {self.object.numero}'
        context['action'] = 'Editar'
        context['solicitud'] = self.object

        # Seleccionar el formset correcto según el tipo de solicitud
        if self.object.tipo == 'ARTICULO':
            context['tipo'] = 'ARTICULO'
            if self.request.POST:
                context['formset'] = DetalleSolicitudArticuloFormSet(self.request.POST, instance=self.object)
            else:
                context['formset'] = DetalleSolicitudArticuloFormSet(instance=self.object)
        else:  # ACTIVO
            context['tipo'] = 'ACTIVO'
            if self.request.POST:
                context['formset'] = DetalleSolicitudActivoFormSet(self.request.POST, instance=self.object)
            else:
                context['formset'] = DetalleSolicitudActivoFormSet(instance=self.object)

        return context

    def get_template_names(self):
        # Si la petición es AJAX o se solicita modal, devolver plantilla parcial del formulario
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('modal') == '1':
            return ['solicitudes/partials/modal_form.html']
        return [self.template_name]

    def form_valid(self, form):
        """Procesa el formulario válido con formset.

        Si la petición es AJAX, devuelve el detalle actualizado renderizado en parcial
        para que el frontend lo reemplace dentro del modal o cierre el modal.
        """
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            # Guardar manualmente para controlar la respuesta en AJAX
            form.save()
            formset.save()

            # Log de auditoría
            self.log_action(self.object, self.request)

            # Si es petición AJAX, devolver el detalle parcial para mostrar en modal
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('modal') == '1':
                # Construir contexto usando la DetailView para mantener consistencia
                detalle_view = SolicitudDetailView()
                detalle_view.request = self.request
                detalle_view.object = self.object
                detalle_context = detalle_view.get_context_data()
                return render(self.request, 'solicitudes/partials/modal_detalle.html', detalle_context)

            return super().form_valid(form)
        else:
            # Si es AJAX, re-renderizar el formulario con errores para inyectarlo en el modal
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('modal') == '1':
                return render(self.request, 'solicitudes/partials/modal_form.html', context)
            return self.form_invalid(form)


class SolicitudDeleteView(EliminarMisSolicitudesPermissionMixin, BaseAuditedViewMixin, AtomicTransactionMixin, DeleteView):
    """
    Vista para eliminar una solicitud (MIS SOLICITUDES).

    Permisos: solicitudes.eliminar_mis_solicitudes (si es el solicitante)
             o solicitudes.eliminar_cualquier_solicitud (si es gestor)
    Auditoría: Registra acción ELIMINAR automáticamente
    Transacción atómica: Garantiza consistencia
    """
    model = Solicitud
    template_name = 'solicitudes/eliminar_solicitud.html'
    success_url = reverse_lazy('solicitudes:lista_solicitudes')

    # Configuración de auditoría
    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó solicitud {obj.numero}'

    # Mensaje de éxito
    success_message = 'Solicitud {obj.numero} eliminada exitosamente.'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Solicitud {self.object.numero}'
        context['solicitud'] = self.object
        return context

    def delete(self, request, *args, **kwargs):
        """Procesa la eliminación con log de auditoría."""
        self.object = self.get_object()
        numero = self.object.numero

        # Eliminar
        response = super().delete(request, *args, **kwargs)

        # Log de auditoría (usar número guardado)
        registrar_log_auditoria(
            usuario=request.user,
            accion_glosa='ELIMINAR',
            descripcion=f'Eliminó solicitud {numero}',
            request=request
        )

        messages.success(request, f'Solicitud {numero} eliminada exitosamente.')
        return response


# ==================== VISTAS DE WORKFLOW (APROBAR, RECHAZAR, DESPACHAR) ====================

class SolicitudAprobarView(AprobarSolicitudesPermissionMixin, BaseAuditedViewMixin, AtomicTransactionMixin, DetailView):
    """
    Vista para aprobar una solicitud (GESTIÓN).

    Permisos: solicitudes.aprobar_solicitudes
    Auditoría: Registra acción APROBAR automáticamente
    Transacción atómica: Garantiza consistencia del workflow
    """
    model = Solicitud
    template_name = 'solicitudes/aprobar_solicitud.html'
    context_object_name = 'solicitud'

    # Configuración de auditoría
    audit_action = 'APROBAR'
    audit_description_template = 'Aprobó solicitud {obj.numero}'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega formulario y datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Aprobar Solicitud {self.object.numero}'

        if self.request.POST:
            context['form'] = AprobarSolicitudForm(self.request.POST, solicitud=self.object)
        else:
            context['form'] = AprobarSolicitudForm(solicitud=self.object)

        return context

    def get(self, request, *args, **kwargs):
        """Verifica que la solicitud pueda ser aprobada."""
        self.object = self.get_object()

        # Verificar que no esté ya aprobada
        if self.object.aprobador:
            messages.warning(request, 'Esta solicitud ya fue aprobada.')
            return redirect('solicitudes:detalle_solicitud', pk=self.object.pk)

        # Verificar que esté en estado PENDIENTE
        if self.object.estado.codigo != 'PENDIENTE':
            messages.warning(request, f'Esta solicitud está en estado {self.object.estado.nombre} y no puede ser aprobada.')
            return redirect('solicitudes:detalle_solicitud', pk=self.object.pk)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Procesa la aprobación de la solicitud usando SolicitudService."""
        self.object = self.get_object()
        form = AprobarSolicitudForm(request.POST, solicitud=self.object)

        if form.is_valid():
            solicitud_service = SolicitudService()

            # Preparar detalles aprobados
            detalles_aprobados = []
            for detalle in self.object.detalles.all():
                field_name = f'cantidad_aprobada_{detalle.id}'
                if field_name in form.cleaned_data:
                    detalles_aprobados.append({
                        'detalle_id': detalle.id,
                        'cantidad_aprobada': form.cleaned_data[field_name]
                    })

            try:
                # Aprobar usando service
                self.object = solicitud_service.aprobar_solicitud(
                    solicitud=self.object,
                    aprobador=request.user,
                    detalles_aprobados=detalles_aprobados,
                    notas_aprobacion=form.cleaned_data.get('notas_aprobacion', '')
                )

                # Log de auditoría
                self.log_action(self.object, request)

                messages.success(request, f'Solicitud {self.object.numero} aprobada exitosamente.')
                return redirect('solicitudes:detalle_solicitud', pk=self.object.pk)

            except ValidationError as e:
                error_msg = str(e.message_dict.get('__all__', [e])[0]) if hasattr(e, 'message_dict') else str(e)
                messages.error(request, error_msg)
                return self.render_to_response(self.get_context_data(form=form))

        # Si el formulario no es válido, mostrar errores
        return self.render_to_response(self.get_context_data(form=form))


class SolicitudRechazarView(RechazarSolicitudesPermissionMixin, BaseAuditedViewMixin, AtomicTransactionMixin, View):
    """
    Vista para rechazar una solicitud (GESTIÓN).

    Permisos: solicitudes.rechazar_solicitudes
    Auditoría: Registra acción RECHAZAR automáticamente
    Transacción atómica: Garantiza consistencia del workflow
    """

    # Configuración de auditoría
    audit_action = 'RECHAZAR'
    audit_description_template = 'Rechazó solicitud {obj.numero}'

    def post(self, request, pk):
        """Procesa el rechazo de la solicitud cambiando solo el estado."""
        try:
            solicitud = Solicitud.objects.get(pk=pk)
        except Solicitud.DoesNotExist:
            messages.error(request, 'Solicitud no encontrada.')
            return redirect('solicitudes:lista_solicitudes')

        # Verificar que no esté finalizada
        if solicitud.estado.es_final:
            messages.warning(request, 'No se puede rechazar una solicitud finalizada.')
            return redirect('solicitudes:detalle_solicitud', pk=solicitud.pk)

        try:
            solicitud_service = SolicitudService()

            # Cambiar estado a RECHAZAR
            estado_rechazado = solicitud_service.estado_repo.get_by_codigo('RECHAZAR')
            if not estado_rechazado:
                raise ValidationError('No existe el estado RECHAZAR en el sistema')

            # Cambiar estado usando el servicio genérico
            solicitud = solicitud_service.cambiar_estado(
                solicitud=solicitud,
                nuevo_estado=estado_rechazado,
                usuario=request.user,
                observaciones=f'Rechazada por {request.user.get_full_name()}'
            )

            # Log de auditoría
            self.log_action(solicitud, request)

            messages.success(request, f'Solicitud {solicitud.numero} rechazada exitosamente.')

        except ValidationError as e:
            error_msg = str(e.message_dict.get('__all__', [e])[0]) if hasattr(e, 'message_dict') else str(e)
            messages.error(request, error_msg)

        # Si es petición AJAX/modal, devolver el partial actualizado
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('modal') == '1':
            from .repositories import HistorialSolicitudRepository
            historial_repo = HistorialSolicitudRepository()
            context = {
                'solicitud': solicitud,
                'detalles': solicitud.detalles.filter(eliminado=False).select_related(
                    'articulo', 'articulo__categoria', 'activo', 'activo__categoria'
                ).order_by('id'),
                'historial': historial_repo.filter_by_solicitud(solicitud)
            }
            return render(request, 'solicitudes/partials/modal_detalle.html', context)

        return redirect('solicitudes:detalle_solicitud', pk=solicitud.pk)


class SolicitudDespacharView(DespacharSolicitudesPermissionMixin, BaseAuditedViewMixin, AtomicTransactionMixin, View):
    """
    Vista para despachar una solicitud (GESTIÓN).

    Permisos: solicitudes.despachar_solicitudes
    Auditoría: Registra acción DESPACHAR automáticamente
    Transacción atómica: Garantiza consistencia del workflow
    """

    # Configuración de auditoría
    audit_action = 'DESPACHAR'
    audit_description_template = 'Despachó solicitud {obj.numero}'

    def post(self, request, pk):
        """Procesa el despacho de la solicitud cambiando el estado a Para Despachar."""
        try:
            solicitud = Solicitud.objects.get(pk=pk)
        except Solicitud.DoesNotExist:
            messages.error(request, 'Solicitud no encontrada.')
            return redirect('solicitudes:lista_solicitudes')

        # Verificar que no esté finalizada
        if solicitud.estado.es_final:
            messages.warning(request, 'No se puede cambiar el estado de una solicitud finalizada.')
            return redirect('solicitudes:detalle_solicitud', pk=solicitud.pk)

        try:
            solicitud_service = SolicitudService()

            # Cambiar estado a DESPACHAR (Para Despachar)
            estado_despachar = solicitud_service.estado_repo.get_by_codigo('DESPACHAR')
            if not estado_despachar:
                raise ValidationError('No existe el estado DESPACHAR en el sistema')

            # Cambiar estado usando el servicio genérico
            solicitud = solicitud_service.cambiar_estado(
                solicitud=solicitud,
                nuevo_estado=estado_despachar,
                usuario=request.user,
                observaciones=f'Marcada para despachar por {request.user.get_full_name()}'
            )

            # Log de auditoría
            self.log_action(solicitud, request)

            messages.success(request, f'Solicitud {solicitud.numero} marcada para despachar.')

        except ValidationError as e:
            error_msg = str(e.message_dict.get('__all__', [e])[0]) if hasattr(e, 'message_dict') else str(e)
            messages.error(request, error_msg)

        # Si es petición AJAX/modal, devolver el partial actualizado
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('modal') == '1':
            from .repositories import HistorialSolicitudRepository
            historial_repo = HistorialSolicitudRepository()
            context = {
                'solicitud': solicitud,
                'detalles': solicitud.detalles.filter(eliminado=False).select_related(
                    'articulo', 'articulo__categoria', 'activo', 'activo__categoria'
                ).order_by('id'),
                'historial': historial_repo.filter_by_solicitud(solicitud)
            }
            return render(request, 'solicitudes/partials/modal_detalle.html', context)

        return redirect('solicitudes:detalle_solicitud', pk=solicitud.pk)


class SolicitudComprarView(DespacharSolicitudesPermissionMixin, BaseAuditedViewMixin, AtomicTransactionMixin, View):
    """
    Vista para marcar una solicitud como comprada (en proceso de compra).

    Permisos: solicitudes.despachar_solicitudes (mismo permiso que despachar)
    Auditoría: Registra acción COMPRAR automáticamente
    Transacción atómica: Garantiza consistencia del workflow
    """

    # Configuración de auditoría
    audit_action = 'COMPRAR'
    audit_description_template = 'Envió a compras la solicitud {obj.numero}'

    def post(self, request, pk):
        """Procesa el envío de la solicitud a compras usando SolicitudService."""
        try:
            solicitud = Solicitud.objects.get(pk=pk)
        except Solicitud.DoesNotExist:
            messages.error(request, 'Solicitud no encontrada.')
            return redirect('solicitudes:lista_solicitudes')

        # Verificar que no esté finalizada
        if solicitud.estado.es_final:
            messages.warning(request, 'No se puede enviar a compras una solicitud finalizada.')
            return redirect('solicitudes:detalle_solicitud', pk=solicitud.pk)

        try:
            solicitud_service = SolicitudService()

            # Marcar como comprada usando service
            solicitud = solicitud_service.comprar_solicitud(
                solicitud=solicitud,
                comprador=request.user,
                notas_compra=request.POST.get('notas_compra', '')
            )

            # Log de auditoría
            self.log_action(solicitud, request)

            messages.success(request, f'Solicitud {solicitud.numero} enviada a compras exitosamente.')

        except ValidationError as e:
            error_msg = str(e.message_dict.get('__all__', [e])[0]) if hasattr(e, 'message_dict') else str(e)
            messages.error(request, error_msg)

        # Si es petición AJAX/modal, devolver el partial actualizado
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('modal') == '1':
            from .repositories import HistorialSolicitudRepository
            historial_repo = HistorialSolicitudRepository()
            context = {
                'solicitud': solicitud,
                'detalles': solicitud.detalles.filter(eliminado=False).select_related(
                    'articulo', 'articulo__categoria', 'activo', 'activo__categoria'
                ).order_by('id'),
                'historial': historial_repo.filter_by_solicitud(solicitud)
            }
            return render(request, 'solicitudes/partials/modal_detalle.html', context)

        return redirect('solicitudes:detalle_solicitud', pk=solicitud.pk)


# ==================== VISTAS ESPECÍFICAS PARA ACTIVOS ====================

class SolicitudActivoListView(VerSolicitudesBienesPermissionMixin, SolicitudListView):
    """
    Vista para listar solicitudes de activos/bienes (SOLICITUD BIENES).

    Permisos: solicitudes.ver_solicitudes_bienes
    """
    template_name = 'solicitudes/lista_solicitudes_activos.html'

    def get_queryset(self) -> QuerySet:
        """Filtra solo solicitudes de activos."""
        return super().get_queryset().filter(tipo='ACTIVO')

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Solicitudes de Activos/Bienes'
        context['tipo'] = 'ACTIVO'
        return context


class SolicitudActivoCreateView(CrearSolicitudBienesPermissionMixin, SolicitudCreateView):
    """
    Vista para crear una nueva solicitud de bienes (SOLICITUD BIENES).

    Permisos: solicitudes.crear_solicitud_bienes
    """
    template_name = 'solicitudes/form_solicitud_bienes.html'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto y lista de activos disponibles."""
        from apps.activos.models import Activo

        context = super(SolicitudCreateView, self).get_context_data(**kwargs)
        context['titulo'] = 'Crear Solicitud de Bienes'
        context['action'] = 'Crear'
        context['tipo'] = 'ACTIVO'

        # Agregar lista de activos disponibles para el modal
        context['activos'] = Activo.objects.filter(
            activo=True, eliminado=False
        ).select_related('categoria').order_by('codigo')

        return context

    def form_valid(self, form):
        """Procesa el formulario válido usando SolicitudService con tipo ACTIVO."""
        from django.db import transaction

        try:
            with transaction.atomic():
                # Crear solicitud usando service con tipo ACTIVO
                solicitud_service = SolicitudService()
                self.object = solicitud_service.crear_solicitud(
                    tipo_solicitud=form.cleaned_data['tipo_solicitud'],
                    solicitante=self.request.user,
                    fecha_requerida=form.cleaned_data['fecha_requerida'],
                    motivo=form.cleaned_data['motivo'],
                    titulo_actividad=form.cleaned_data.get('titulo_actividad', ''),
                    objetivo_actividad=form.cleaned_data.get('objetivo_actividad', ''),
                    tipo_choice='ACTIVO',  # FORZAR TIPO ACTIVO
                    bodega_origen=None,  # Los bienes no tienen bodega
                    departamento=form.cleaned_data.get('departamento'),
                    area=form.cleaned_data.get('area'),
                    equipo=form.cleaned_data.get('equipo'),
                    observaciones=form.cleaned_data.get('observaciones', '')
                )

                # Procesar detalles de bienes desde el POST
                detalles = self._extraer_detalles_post(self.request.POST)

                if not detalles:
                    form.add_error(None, 'Debe agregar al menos un bien/activo a la solicitud')
                    return self.form_invalid(form)

                # Crear detalles de bienes
                for detalle_data in detalles:
                    DetalleSolicitud.objects.create(
                        solicitud=self.object,
                        activo_id=detalle_data['activo_id'],
                        cantidad_solicitada=Decimal(str(detalle_data['cantidad_solicitada'])),
                        observaciones=detalle_data.get('observaciones', '')
                    )

                # Mensaje de éxito y log de auditoría
                messages.success(self.request, self.get_success_message(self.object))
                self.log_action(self.object, self.request)

                return redirect(self.get_success_url())

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field if field != '__all__' else None, error)
            return self.form_invalid(form)
        except Exception as e:
            form.add_error(None, f'Error al crear la solicitud: {str(e)}')
            return self.form_invalid(form)

    def _extraer_detalles_post(self, post_data):
        """
        Extrae los detalles de bienes del POST.
        Formato esperado: detalles[0][activo_id], detalles[0][cantidad_solicitada], etc.
        """
        detalles = []
        indices = set()

        # Identificar todos los índices presentes
        for key in post_data.keys():
            if key.startswith('detalles['):
                # Extraer índice: detalles[0][campo] -> 0
                indice = key.split('[')[1].split(']')[0]
                indices.add(indice)

        # Extraer datos para cada índice
        for indice in indices:
            activo_id = post_data.get(f'detalles[{indice}][activo_id]')
            cantidad_solicitada = post_data.get(f'detalles[{indice}][cantidad_solicitada]')

            if activo_id and cantidad_solicitada:
                detalle = {
                    'activo_id': int(activo_id),
                    'cantidad_solicitada': float(cantidad_solicitada),
                    'observaciones': post_data.get(f'detalles[{indice}][observaciones]', '')
                }

                detalles.append(detalle)

        return detalles


class SolicitudActivoUpdateView(SolicitudUpdateView):
    """Vista para editar una solicitud de bienes."""
    template_name = 'solicitudes/form_solicitud.html'

    def get_queryset(self) -> QuerySet:
        """Solo solicitudes de bienes."""
        return super().get_queryset().filter(tipo='ACTIVO')

    def get(self, request, *args, **kwargs):
        """Verifica que la solicitud pueda ser editada."""
        self.object = self.get_object()

        # Solo se pueden editar si están en estado pendiente o rechazada
        if self.object.estado.codigo not in ['PENDIENTE', 'RECHAZADA']:
            messages.error(request, 'Solo se pueden editar solicitudes en estado Pendiente o Rechazada.')
            return redirect('solicitudes:detalle_solicitud', pk=self.object.pk)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto y formset de BIENES."""
        context = super(SolicitudUpdateView, self).get_context_data(**kwargs)
        context['titulo'] = f'Editar Solicitud de Bienes {self.object.numero}'
        context['action'] = 'Editar'
        context['tipo'] = 'ACTIVO'
        context['solicitud'] = self.object

        # Usar formset de BIENES/ACTIVOS
        if self.request.POST:
            context['formset'] = DetalleSolicitudActivoFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = DetalleSolicitudActivoFormSet(instance=self.object)

        return context

    def form_valid(self, form):
        """Asegura que no tenga bodega."""
        form.instance.bodega_origen = None
        return super().form_valid(form)


# ==================== VISTAS ESPECÍFICAS PARA ARTÍCULOS ====================

class SolicitudArticuloListView(VerSolicitudesArticulosPermissionMixin, SolicitudListView):
    """
    Vista para listar solicitudes de artículos (SOLICITUD ARTÍCULOS).

    Permisos: solicitudes.ver_solicitudes_articulos
    """
    template_name = 'solicitudes/lista_solicitudes_articulos.html'

    def get_queryset(self) -> QuerySet:
        """Filtra solo solicitudes de artículos."""
        return super().get_queryset().filter(tipo='ARTICULO')

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Solicitudes de Artículos'
        context['tipo'] = 'ARTICULO'
        return context


class SolicitudArticuloCreateView(CrearSolicitudArticulosPermissionMixin, SolicitudCreateView):
    """
    Vista para crear una nueva solicitud de artículos (SOLICITUD ARTÍCULOS).

    Permisos: solicitudes.crear_solicitud_articulos
    """
    template_name = 'solicitudes/form_solicitud_articulos.html'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto y lista de artículos disponibles."""
        from apps.bodega.models import Articulo

        context = super(SolicitudCreateView, self).get_context_data(**kwargs)
        context['titulo'] = 'Crear Solicitud de Artículos'
        context['action'] = 'Crear'
        context['tipo'] = 'ARTICULO'

        # Agregar lista de artículos disponibles para el modal
        context['articulos'] = Articulo.objects.filter(
            activo=True, eliminado=False
        ).select_related('categoria', 'unidad_medida').order_by('codigo')

        return context

    def form_valid(self, form):
        """Procesa el formulario válido usando SolicitudService con tipo ARTICULO."""
        from django.db import transaction

        try:
            with transaction.atomic():
                # Crear solicitud usando service con tipo ARTICULO
                solicitud_service = SolicitudService()
                self.object = solicitud_service.crear_solicitud(
                    tipo_solicitud=form.cleaned_data['tipo_solicitud'],
                    solicitante=self.request.user,
                    fecha_requerida=form.cleaned_data['fecha_requerida'],
                    motivo=form.cleaned_data['motivo'],
                    titulo_actividad=form.cleaned_data.get('titulo_actividad', ''),
                    objetivo_actividad=form.cleaned_data.get('objetivo_actividad', ''),
                    tipo_choice='ARTICULO',  # FORZAR TIPO ARTICULO
                    bodega_origen=form.cleaned_data.get('bodega_origen'),
                    departamento=form.cleaned_data.get('departamento'),
                    area=form.cleaned_data.get('area'),
                    equipo=form.cleaned_data.get('equipo'),
                    observaciones=form.cleaned_data.get('observaciones', '')
                )

                # Procesar detalles de artículos desde el POST
                detalles = self._extraer_detalles_post(self.request.POST)

                if not detalles:
                    form.add_error(None, 'Debe agregar al menos un artículo a la solicitud')
                    return self.form_invalid(form)

                # Crear detalles de artículos
                for detalle_data in detalles:
                    DetalleSolicitud.objects.create(
                        solicitud=self.object,
                        articulo_id=detalle_data['articulo_id'],
                        cantidad_solicitada=Decimal(str(detalle_data['cantidad_solicitada'])),
                        observaciones=detalle_data.get('observaciones', '')
                    )

                # Mensaje de éxito y log de auditoría
                messages.success(self.request, self.get_success_message(self.object))
                self.log_action(self.object, self.request)

                return redirect(self.get_success_url())

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field if field != '__all__' else None, error)
            return self.form_invalid(form)
        except Exception as e:
            form.add_error(None, f'Error al crear la solicitud: {str(e)}')
            return self.form_invalid(form)

    def _extraer_detalles_post(self, post_data):
        """
        Extrae los detalles de artículos del POST.
        Formato esperado: detalles[0][articulo_id], detalles[0][cantidad_solicitada], etc.
        """
        detalles = []
        indices = set()

        # Identificar todos los índices presentes
        for key in post_data.keys():
            if key.startswith('detalles['):
                # Extraer índice: detalles[0][campo] -> 0
                indice = key.split('[')[1].split(']')[0]
                indices.add(indice)

        # Extraer datos para cada índice
        for indice in indices:
            articulo_id = post_data.get(f'detalles[{indice}][articulo_id]')
            cantidad_solicitada = post_data.get(f'detalles[{indice}][cantidad_solicitada]')

            if articulo_id and cantidad_solicitada:
                detalle = {
                    'articulo_id': int(articulo_id),
                    'cantidad_solicitada': float(cantidad_solicitada),
                    'observaciones': post_data.get(f'detalles[{indice}][observaciones]', '')
                }

                detalles.append(detalle)

        return detalles


class SolicitudArticuloUpdateView(SolicitudUpdateView):
    """Vista para editar una solicitud de artículos."""
    template_name = 'solicitudes/form_solicitud.html'

    def get_queryset(self) -> QuerySet:
        """Solo solicitudes de artículos."""
        return super().get_queryset().filter(tipo='ARTICULO')

    def get(self, request, *args, **kwargs):
        """Verifica que la solicitud pueda ser editada."""
        self.object = self.get_object()

        # Solo se pueden editar si están en estado pendiente o rechazada
        if self.object.estado.codigo not in ['PENDIENTE', 'RECHAZADA']:
            messages.error(request, 'Solo se pueden editar solicitudes en estado Pendiente o Rechazada.')
            return redirect('solicitudes:detalle_solicitud', pk=self.object.pk)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto y formset de ARTÍCULOS."""
        context = super(SolicitudUpdateView, self).get_context_data(**kwargs)
        context['titulo'] = f'Editar Solicitud de Artículos {self.object.numero}'
        context['action'] = 'Editar'
        context['tipo'] = 'ARTICULO'
        context['solicitud'] = self.object

        # Usar formset de ARTÍCULOS
        if self.request.POST:
            context['formset'] = DetalleSolicitudArticuloFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = DetalleSolicitudArticuloFormSet(instance=self.object)

        return context


# ==================== VISTAS MANTENEDORES: TIPOS DE SOLICITUD ====================


class TipoSolicitudListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para listar tipos de solicitud.

    Permisos: solicitudes.view_tiposolicitud
    Utiliza: TipoSolicitudRepository para acceso a datos optimizado
    """
    model = TipoSolicitud
    template_name = 'solicitudes/mantenedores/tipo_solicitud/lista.html'
    context_object_name = 'tipos'
    permission_required = 'solicitudes.view_tiposolicitud'
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        """Retorna tipos de solicitud usando repository."""
        from .repositories import TipoSolicitudRepository
        tipo_repo = TipoSolicitudRepository()

        # Incluir inactivos y eliminados para administración
        queryset = TipoSolicitud.objects.filter(eliminado=False).order_by('codigo')

        # Búsqueda por query string
        query = self.request.GET.get('q', '').strip()
        if query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(codigo__icontains=query) |
                Q(nombre__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Tipos de Solicitud'
        context['puede_crear'] = self.request.user.has_perm('solicitudes.add_tiposolicitud')
        return context


class TipoSolicitudCreateView(BaseAuditedViewMixin, CreateView):
    """
    Vista para crear un nuevo tipo de solicitud.

    Permisos: solicitudes.add_tiposolicitud
    Auditoría: Registra acción CREAR automáticamente
    """
    model = TipoSolicitud
    form_class = TipoSolicitudForm
    template_name = 'solicitudes/mantenedores/tipo_solicitud/form.html'
    permission_required = 'solicitudes.add_tiposolicitud'
    success_url = reverse_lazy('solicitudes:tipo_solicitud_lista')

    # Configuración de auditoría
    audit_action = 'CREAR'
    audit_description_template = 'Creó tipo de solicitud {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Tipo de solicitud {obj.nombre} creado exitosamente.'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Tipo de Solicitud'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message(self.object))
        self.log_action(self.object, self.request)
        return response


class TipoSolicitudUpdateView(BaseAuditedViewMixin, UpdateView):
    """
    Vista para editar un tipo de solicitud existente.

    Permisos: solicitudes.change_tiposolicitud
    Auditoría: Registra acción EDITAR automáticamente
    """
    model = TipoSolicitud
    form_class = TipoSolicitudForm
    template_name = 'solicitudes/mantenedores/tipo_solicitud/form.html'
    permission_required = 'solicitudes.change_tiposolicitud'
    success_url = reverse_lazy('solicitudes:tipo_solicitud_lista')

    # Configuración de auditoría
    audit_action = 'EDITAR'
    audit_description_template = 'Editó tipo de solicitud {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Tipo de solicitud {obj.nombre} actualizado exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite editar tipos no eliminados."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Tipo de Solicitud: {self.object.nombre}'
        context['action'] = 'Actualizar'
        context['tipo'] = self.object
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message(self.object))
        self.log_action(self.object, self.request)
        return response


class TipoSolicitudDeleteView(BaseAuditedViewMixin, DeleteView):
    """
    Vista para eliminar (soft delete) un tipo de solicitud.

    Permisos: solicitudes.delete_tiposolicitud
    Auditoría: Registra acción ELIMINAR automáticamente
    """
    model = TipoSolicitud
    template_name = 'solicitudes/mantenedores/tipo_solicitud/eliminar.html'
    permission_required = 'solicitudes.delete_tiposolicitud'
    success_url = reverse_lazy('solicitudes:tipo_solicitud_lista')

    # Configuración de auditoría
    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó tipo de solicitud {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Tipo de solicitud {obj.nombre} eliminado exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite eliminar tipos no eliminados."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Tipo de Solicitud: {self.object.nombre}'
        context['tipo'] = self.object

        # Verificar si hay solicitudes asociadas
        context['tiene_solicitudes'] = self.object.solicitudes.filter(eliminado=False).exists()
        context['count_solicitudes'] = self.object.solicitudes.filter(eliminado=False).count()

        return context

    def delete(self, request, *args, **kwargs):
        """Elimina usando soft delete."""
        self.object = self.get_object()

        # Verificar si tiene solicitudes asociadas
        if self.object.solicitudes.filter(eliminado=False).exists():
            messages.error(
                request,
                f'No se puede eliminar el tipo "{self.object.nombre}" porque tiene solicitudes asociadas. '
                'Desactívelo en su lugar.'
            )
            return redirect('solicitudes:tipo_solicitud_lista')

        # Soft delete
        self.object.eliminado = True
        self.object.activo = False
        self.object.save()

        messages.success(request, self.get_success_message(self.object))
        self.log_action(self.object, request)

        return redirect(self.success_url)


# ==================== VISTAS MANTENEDORES: ESTADOS DE SOLICITUD ====================


class EstadoSolicitudListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para listar estados de solicitud.

    Permisos: solicitudes.view_estadosolicitud
    Utiliza: EstadoSolicitudRepository para acceso a datos optimizado
    """
    model = EstadoSolicitud
    template_name = 'solicitudes/mantenedores/estado_solicitud/lista.html'
    context_object_name = 'estados'
    permission_required = 'solicitudes.view_estadosolicitud'
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        """Retorna estados de solicitud usando repository."""
        from .repositories import EstadoSolicitudRepository
        estado_repo = EstadoSolicitudRepository()

        # Incluir inactivos y eliminados para administración
        queryset = EstadoSolicitud.objects.filter(eliminado=False).order_by('codigo')

        # Búsqueda por query string
        query = self.request.GET.get('q', '').strip()
        if query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(codigo__icontains=query) |
                Q(nombre__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Estados de Solicitud'
        context['puede_crear'] = self.request.user.has_perm('solicitudes.add_estadosolicitud')
        return context


class EstadoSolicitudCreateView(BaseAuditedViewMixin, CreateView):
    """
    Vista para crear un nuevo estado de solicitud.

    Permisos: solicitudes.add_estadosolicitud
    Auditoría: Registra acción CREAR automáticamente
    """
    model = EstadoSolicitud
    form_class = EstadoSolicitudForm
    template_name = 'solicitudes/mantenedores/estado_solicitud/form.html'
    permission_required = 'solicitudes.add_estadosolicitud'
    success_url = reverse_lazy('solicitudes:estado_solicitud_lista')

    # Configuración de auditoría
    audit_action = 'CREAR'
    audit_description_template = 'Creó estado de solicitud {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Estado de solicitud {obj.nombre} creado exitosamente.'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Estado de Solicitud'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message(self.object))
        self.log_action(self.object, self.request)
        return response


class EstadoSolicitudUpdateView(BaseAuditedViewMixin, UpdateView):
    """
    Vista para editar un estado de solicitud existente.

    Permisos: solicitudes.change_estadosolicitud
    Auditoría: Registra acción EDITAR automáticamente
    """
    model = EstadoSolicitud
    form_class = EstadoSolicitudForm
    template_name = 'solicitudes/mantenedores/estado_solicitud/form.html'
    permission_required = 'solicitudes.change_estadosolicitud'
    success_url = reverse_lazy('solicitudes:estado_solicitud_lista')

    # Configuración de auditoría
    audit_action = 'EDITAR'
    audit_description_template = 'Editó estado de solicitud {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Estado de solicitud {obj.nombre} actualizado exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite editar estados no eliminados."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Estado de Solicitud: {self.object.nombre}'
        context['action'] = 'Actualizar'
        context['estado'] = self.object
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message(self.object))
        self.log_action(self.object, self.request)
        return response


class EstadoSolicitudDeleteView(BaseAuditedViewMixin, DeleteView):
    """
    Vista para eliminar (soft delete) un estado de solicitud.

    Permisos: solicitudes.delete_estadosolicitud
    Auditoría: Registra acción ELIMINAR automáticamente
    """
    model = EstadoSolicitud
    template_name = 'solicitudes/mantenedores/estado_solicitud/eliminar.html'
    permission_required = 'solicitudes.delete_estadosolicitud'
    success_url = reverse_lazy('solicitudes:estado_solicitud_lista')

    # Configuración de auditoría
    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó estado de solicitud {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Estado de solicitud {obj.nombre} eliminado exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite eliminar estados no eliminados."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Estado de Solicitud: {self.object.nombre}'
        context['estado'] = self.object

        # Verificar si hay solicitudes asociadas
        context['tiene_solicitudes'] = self.object.solicitudes.filter(eliminado=False).exists()
        context['count_solicitudes'] = self.object.solicitudes.filter(eliminado=False).count()

        return context

    def delete(self, request, *args, **kwargs):
        """Elimina usando soft delete."""
        self.object = self.get_object()

        # Verificar si tiene solicitudes asociadas
        if self.object.solicitudes.filter(eliminado=False).exists():
            messages.error(
                request,
                f'No se puede eliminar el estado "{self.object.nombre}" porque tiene solicitudes asociadas. '
                'Desactívelo en su lugar.'
            )
            return redirect('solicitudes:estado_solicitud_lista')

        # Soft delete
        self.object.eliminado = True
        self.object.activo = False
        self.object.save()

        messages.success(request, self.get_success_message(self.object))
        self.log_action(self.object, request)

        return redirect(self.success_url)


# ==================== IMPORTACION EXCEL PARA MANTENEDORES ====================

from apps.bodega.excel_services.importacion_excel import ImportacionExcelService
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required


@login_required
def tipo_solicitud_descargar_plantilla(request):
    """Vista para descargar plantilla Excel de tipos de solicitud."""
    contenido = ImportacionExcelService.generar_plantilla_tipos_solicitud()
    response = HttpResponse(contenido, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="plantilla_tipos_solicitud.xlsx"'
    return response


@login_required
def tipo_solicitud_importar_excel(request):
    """Vista para importar tipos de solicitud desde Excel."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)
    if 'archivo' not in request.FILES:
        return JsonResponse({'error': 'No se proporciono archivo'}, status=400)
    archivo = request.FILES['archivo']
    es_valido, mensaje_error = ImportacionExcelService.validar_archivo_excel(archivo)
    if not es_valido:
        return JsonResponse({'error': mensaje_error}, status=400)
    try:
        creadas, actualizadas, errores = ImportacionExcelService.importar_tipos_solicitud(archivo, request.user)
        mensaje = f"Importacion completada: {creadas} tipos creados, {actualizadas} actualizados"
        if errores:
            mensaje += f". Errores: {len(errores)}"
        return JsonResponse({
            'success': True,
            'mensaje': mensaje,
            'creadas': creadas,
            'actualizadas': actualizadas,
            'errores': errores[:10]
        })
    except Exception as e:
        return JsonResponse({'error': f'Error al importar: {str(e)}'}, status=500)


@login_required
def estado_solicitud_descargar_plantilla(request):
    """Vista para descargar plantilla Excel de estados de solicitud."""
    contenido = ImportacionExcelService.generar_plantilla_estados_solicitud()
    response = HttpResponse(contenido, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="plantilla_estados_solicitud.xlsx"'
    return response


@login_required
def estado_solicitud_importar_excel(request):
    """Vista para importar estados de solicitud desde Excel."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)
    if 'archivo' not in request.FILES:
        return JsonResponse({'error': 'No se proporciono archivo'}, status=400)
    archivo = request.FILES['archivo']
    es_valido, mensaje_error = ImportacionExcelService.validar_archivo_excel(archivo)
    if not es_valido:
        return JsonResponse({'error': mensaje_error}, status=400)
    try:
        creadas, actualizadas, errores = ImportacionExcelService.importar_estados_solicitud(archivo, request.user)
        mensaje = f"Importacion completada: {creadas} estados creados, {actualizadas} actualizados"
        if errores:
            mensaje += f". Errores: {len(errores)}"
        return JsonResponse({
            'success': True,
            'mensaje': mensaje,
            'creadas': creadas,
            'actualizadas': actualizadas,
            'errores': errores[:10]
        })
    except Exception as e:
        return JsonResponse({'error': f'Error al importar: {str(e)}'}, status=500)
