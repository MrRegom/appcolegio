"""
Class-Based Views para el módulo de bodega.

Implementa las mejores prácticas con CBVs siguiendo SOLID y DRY:
- Reutilización de mixins
- Separación de responsabilidades (vistas delgadas, lógica en services)
- Repository Pattern para acceso a datos
- Service Layer para lógica de negocio
- Código más limpio y mantenible
- Type hints completos
- Paginación automática
- Auditoría automática
"""
from typing import Any, Optional
from django.db.models import QuerySet, Q, Sum, Count
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponse, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from core.mixins import (
    BaseAuditedViewMixin, AtomicTransactionMixin, SoftDeleteMixin,
    PaginatedListMixin, FilteredListMixin
)
from .models import (
    Bodega, UnidadMedida, Categoria, Marca, Articulo, Operacion,
    TipoMovimiento, Movimiento, TipoEntrega, EstadoEntrega,
    EntregaArticulo, EntregaBien
)
from .forms import (
    UnidadMedidaForm, CategoriaForm, MarcaForm, ArticuloForm,
    OperacionForm, TipoMovimientoForm, MovimientoForm, ArticuloFiltroForm,
    EntregaArticuloForm, EntregaBienForm
)
from .repositories import (
    BodegaRepository, CategoriaRepository, MarcaRepository,
    ArticuloRepository, OperacionRepository, TipoMovimientoRepository,
    MovimientoRepository, EntregaArticuloRepository, EntregaBienRepository,
    EstadoEntregaRepository, TipoEntregaRepository
)
from .services import (
    CategoriaService, ArticuloService, MovimientoService,
    EntregaArticuloService, EntregaBienService
)
from .services_importacion_excel import ImportacionExcelService


# ==================== MENÚ PRINCIPAL ====================

class MenuBodegaView(LoginRequiredMixin, TemplateView):
    """
    Vista del menú principal de bodega con estadísticas.

    Muestra cards con resumen de bodega según las mejores prácticas de Django 5.2.
    Usa repositories para obtener estadísticas de manera eficiente.
    """
    template_name = 'bodega/menu_bodega.html'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega estadísticas al contexto usando repositories."""
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Usar repositories para obtener estadísticas
        articulo_repo = ArticuloRepository()
        categoria_repo = CategoriaRepository()
        bodega_repo = BodegaRepository()
        movimiento_repo = MovimientoRepository()
        entrega_articulo_repo = EntregaArticuloRepository()
        entrega_bien_repo = EntregaBienRepository()

        # Estadísticas para el módulo de bodega
        context['stats'] = {
            'total_articulos': articulo_repo.get_all().count(),
            'total_categorias': categoria_repo.get_all().count(),
            'total_movimientos': movimiento_repo.get_all().count(),
            'bodegas_activas': bodega_repo.get_active().count(),
            'stock_total': articulo_repo.get_all().aggregate(
                total=Sum('stock_actual')
            )['total'] or 0,
            'total_entregas_articulos': entrega_articulo_repo.get_all().count(),
            'total_entregas_bienes': entrega_bien_repo.get_all().count(),
        }

        # Permisos del usuario
        context['permisos'] = {
            'puede_crear_articulo': user.has_perm('bodega.add_articulo'),
            'puede_crear_categoria': user.has_perm('bodega.add_categoria'),
            'puede_crear_movimiento': user.has_perm('bodega.add_movimiento'),
            'puede_gestionar': user.has_perm('bodega.change_articulo'),
        }

        context['titulo'] = 'Módulo de Bodega'
        return context


# ==================== VISTAS DE UNIDAD DE MEDIDA ====================

class UnidadMedidaListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para listar unidades de medida con paginación y filtros.

    IMPORTANTE: Este modelo pertenece al módulo de BODEGA, no al módulo de activos.
    Permisos: bodega.view_unidadmedida
    """
    model = UnidadMedida
    template_name = 'bodega/unidad_medida/lista.html'
    context_object_name = 'unidades'
    permission_required = 'bodega.view_unidadmedida'
    paginate_by = 25

    def get_queryset(self) -> QuerySet[UnidadMedida]:
        """Retorna unidades de medida no eliminadas."""
        queryset = super().get_queryset().filter(eliminado=False)

        # Filtro de búsqueda
        q: str = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(codigo__icontains=q) |
                Q(nombre__icontains=q) |
                Q(simbolo__icontains=q)
            )

        return queryset.order_by('codigo')

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Unidades de Medida'
        context['query'] = self.request.GET.get('q', '')
        return context


class UnidadMedidaCreateView(BaseAuditedViewMixin, CreateView):
    """
    Vista para crear una nueva unidad de medida.

    Permisos: bodega.add_unidadmedida
    Auditoría: Registra acción CREAR automáticamente
    """
    model = UnidadMedida
    form_class = UnidadMedidaForm
    template_name = 'bodega/unidad_medida/form.html'
    permission_required = 'bodega.add_unidadmedida'
    success_url = reverse_lazy('bodega:lista_unidades')

    # Configuración de auditoría
    audit_action = 'CREAR'
    audit_description_template = 'Unidad de medida creada: {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Unidad de medida {obj.nombre} creada exitosamente.'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Unidad de Medida'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        self.log_action(self.object, self.request)
        return response


class UnidadMedidaUpdateView(BaseAuditedViewMixin, UpdateView):
    """
    Vista para editar una unidad de medida existente.

    Permisos: bodega.change_unidadmedida
    Auditoría: Registra acción EDITAR automáticamente
    """
    model = UnidadMedida
    form_class = UnidadMedidaForm
    template_name = 'bodega/unidad_medida/form.html'
    permission_required = 'bodega.change_unidadmedida'
    success_url = reverse_lazy('bodega:lista_unidades')

    # Configuración de auditoría
    audit_action = 'EDITAR'
    audit_description_template = 'Unidad de medida actualizada: {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Unidad de medida {obj.nombre} actualizada exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite editar unidades no eliminadas."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Unidad de Medida: {self.object.nombre}'
        context['action'] = 'Actualizar'
        context['unidad'] = self.object
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        self.log_action(self.object, self.request)
        return response


class UnidadMedidaDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """
    Vista para eliminar (soft delete) una unidad de medida.

    Permisos: bodega.delete_unidadmedida
    Auditoría: Registra acción ELIMINAR automáticamente
    Implementa soft delete (marca como eliminado, no borra físicamente)
    """
    model = UnidadMedida
    template_name = 'bodega/unidad_medida/eliminar.html'
    permission_required = 'bodega.delete_unidadmedida'
    success_url = reverse_lazy('bodega:lista_unidades')

    # Configuración de auditoría
    audit_action = 'ELIMINAR'
    audit_description_template = 'Unidad de medida eliminada: {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Unidad de medida {obj.nombre} eliminada exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite eliminar unidades no eliminadas."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Unidad de Medida: {self.object.nombre}'
        context['unidad'] = self.object
        return context


# ==================== VISTAS DE CATEGORÍA ====================

class CategoriaListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para listar categorías con paginación y filtros.

    Permisos: bodega.view_categoria
    Usa CategoriaRepository para acceso a datos
    """
    model = Categoria
    template_name = 'bodega/categoria/lista.html'
    context_object_name = 'categorias'
    permission_required = 'bodega.view_categoria'
    paginate_by = 25

    def get_queryset(self) -> QuerySet[Categoria]:
        """Retorna categorías usando repository."""
        repo = CategoriaRepository()

        # Filtro de búsqueda
        q: str = self.request.GET.get('q', '').strip()
        if q:
            return repo.search(q)

        return repo.get_all()

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Categorías'
        context['query'] = self.request.GET.get('q', '')
        return context


class CategoriaCreateView(BaseAuditedViewMixin, CreateView):
    """
    Vista para crear una nueva categoría.

    Permisos: bodega.add_categoria
    Auditoría: Registra acción CREAR automáticamente
    """
    model = Categoria
    form_class = CategoriaForm
    template_name = 'bodega/categoria/form.html'
    permission_required = 'bodega.add_categoria'
    success_url = reverse_lazy('bodega:categoria_lista')

    # Configuración de auditoría
    audit_action = 'CREAR'
    audit_description_template = 'Categoría creada: {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Categoría {obj.nombre} creada exitosamente.'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Categoría'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        self.log_action(self.object, self.request)
        return response


class CategoriaUpdateView(BaseAuditedViewMixin, UpdateView):
    """
    Vista para editar una categoría existente.

    Permisos: bodega.change_categoria
    Auditoría: Registra acción EDITAR automáticamente
    """
    model = Categoria
    form_class = CategoriaForm
    template_name = 'bodega/categoria/form.html'
    permission_required = 'bodega.change_categoria'
    success_url = reverse_lazy('bodega:categoria_lista')

    # Configuración de auditoría
    audit_action = 'EDITAR'
    audit_description_template = 'Categoría actualizada: {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Categoría {obj.nombre} actualizada exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite editar categorías no eliminadas."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Categoría: {self.object.nombre}'
        context['action'] = 'Actualizar'
        context['categoria'] = self.object
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        self.log_action(self.object, self.request)
        return response


class CategoriaDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """
    Vista para eliminar (soft delete) una categoría.

    Permisos: bodega.delete_categoria
    Auditoría: Registra acción ELIMINAR automáticamente
    Implementa soft delete (marca como eliminado, no borra físicamente)
    """
    model = Categoria
    template_name = 'bodega/categoria/eliminar.html'
    permission_required = 'bodega.delete_categoria'
    success_url = reverse_lazy('bodega:categoria_lista')

    # Configuración de auditoría
    audit_action = 'ELIMINAR'
    audit_description_template = 'Categoría eliminada: {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Categoría {obj.nombre} eliminada exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite eliminar categorías no eliminadas."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Categoría: {self.object.nombre}'
        context['categoria'] = self.object
        # Verificar si tiene artículos
        context['tiene_articulos'] = self.object.articulos.filter(eliminado=False).exists()
        return context


# ==================== VISTAS DE ARTÍCULO ====================

class ArticuloListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para listar artículos con paginación y filtros.

    Permisos: bodega.view_articulo
    Filtros: Categoría, bodega, búsqueda por texto, estado activo
    """
    model = Articulo
    template_name = 'bodega/articulo/lista.html'
    context_object_name = 'articulos'
    permission_required = 'bodega.view_articulo'
    paginate_by = 25
    filter_form_class = ArticuloFiltroForm

    def get_queryset(self) -> QuerySet:
        """
        Retorna artículos no eliminados con relaciones optimizadas.

        Optimización N+1: Usa select_related para evitar queries adicionales.
        """
        queryset = super().get_queryset().filter(
            eliminado=False
        ).select_related(
            'categoria', 'ubicacion_fisica'
        )

        # Aplicar filtros del formulario
        form = self.filter_form_class(self.request.GET)
        if form.is_valid():
            data = form.cleaned_data

            # Filtro de búsqueda por texto
            if data.get('q'):
                q = data['q']
                queryset = queryset.filter(
                    Q(codigo__icontains=q) |
                    Q(nombre__icontains=q) |
                    Q(descripcion__icontains=q)
                )

            # Filtro por categoría
            if data.get('categoria'):
                queryset = queryset.filter(categoria=data['categoria'])

            # Filtro por bodega
            if data.get('bodega'):
                queryset = queryset.filter(ubicacion_fisica=data['bodega'])

            # Filtro por estado activo
            if data.get('activo') != '':
                queryset = queryset.filter(activo=(data['activo'] == '1'))

        return queryset.order_by('codigo')

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Artículos'

        # Agregar categorías y bodegas directamente
        from apps.bodega.models import Categoria as CategoriaModel, Bodega as BodegaModel
        context['categorias'] = CategoriaModel.objects.filter(activo=True, eliminado=False).order_by('nombre')
        context['bodegas'] = BodegaModel.objects.filter(activo=True, eliminado=False).order_by('nombre')

        return context


class ArticuloCreateView(BaseAuditedViewMixin, CreateView):
    """
    Vista para crear un nuevo artículo.

    Permisos: bodega.add_articulo
    Auditoría: Registra acción CREAR automáticamente
    """
    model = Articulo
    form_class = ArticuloForm
    template_name = 'bodega/articulo/form.html'
    permission_required = 'bodega.add_articulo'
    success_url = reverse_lazy('bodega:articulo_lista')

    # Configuración de auditoría
    audit_action = 'CREAR'
    audit_description_template = 'Artículo creado: {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Artículo {obj.codigo} creado exitosamente.'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Artículo'
        context['action'] = 'Crear'

        # Agregar categorías y bodegas para los selectores
        context['categorias'] = Categoria.objects.filter(activo=True, eliminado=False).order_by('nombre')
        context['bodegas'] = Bodega.objects.filter(activo=True, eliminado=False).order_by('nombre')

        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        self.log_action(self.object, self.request)
        return response


class ArticuloUpdateView(BaseAuditedViewMixin, UpdateView):
    """
    Vista para editar un artículo existente.

    Permisos: bodega.change_articulo
    Auditoría: Registra acción EDITAR automáticamente
    """
    model = Articulo
    form_class = ArticuloForm
    template_name = 'bodega/articulo/form.html'
    permission_required = 'bodega.change_articulo'
    success_url = reverse_lazy('bodega:articulo_lista')

    # Configuración de auditoría
    audit_action = 'EDITAR'
    audit_description_template = 'Artículo actualizado: {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Artículo {obj.codigo} actualizado exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite editar artículos no eliminados."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Artículo: {self.object.codigo}'
        context['action'] = 'Actualizar'
        context['articulo'] = self.object

        # Agregar categorías y bodegas para los selectores
        context['categorias'] = Categoria.objects.filter(activo=True, eliminado=False).order_by('nombre')
        context['bodegas'] = Bodega.objects.filter(activo=True, eliminado=False).order_by('nombre')

        # Agregar marcas y unidades de medida para los selectores
        from apps.activos.models import Marca
        context['marcas'] = Marca.objects.filter(activo=True, eliminado=False).order_by('nombre')
        context['unidades'] = UnidadMedida.objects.filter(activo=True, eliminado=False).order_by('codigo')

        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría y mensaje de éxito."""
        # Guardar el formulario (esto ya llama a form.save())
        response = super().form_valid(form)
        # Registrar en auditoría
        self.log_action(self.object, self.request)
        # El mensaje de éxito ya se muestra por SuccessMessageMixin en super().form_valid()
        return response


class ArticuloDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """
    Vista para eliminar (soft delete) un artículo.

    Permisos: bodega.delete_articulo
    Auditoría: Registra acción ELIMINAR automáticamente
    """
    model = Articulo
    template_name = 'bodega/articulo/eliminar.html'
    permission_required = 'bodega.delete_articulo'
    success_url = reverse_lazy('bodega:articulo_lista')

    # Configuración de auditoría
    audit_action = 'ELIMINAR'
    audit_description_template = 'Artículo eliminado: {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Artículo {obj.codigo} eliminado exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite eliminar artículos no eliminados."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Artículo: {self.object.codigo}'
        context['articulo'] = self.object
        return context


class ArticuloDetailView(BaseAuditedViewMixin, DetailView):
    """
    Vista para ver el detalle de un artículo con su historial de movimientos.

    Permisos: bodega.view_articulo
    Usa repositories para acceso optimizado a datos
    """
    model = Articulo
    template_name = 'bodega/articulo/detalle.html'
    context_object_name = 'articulo'
    permission_required = 'bodega.view_articulo'

    def get_queryset(self) -> QuerySet[Articulo]:
        """Usa repository para consultas optimizadas."""
        return ArticuloRepository().get_all()

    def get_context_data(self, **kwargs) -> dict:
        """Agrega movimientos recientes usando MovimientoService."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Detalle Artículo {self.object.codigo}'

        # Usar service para obtener historial
        service = MovimientoService()
        context['movimientos'] = service.obtener_historial_articulo(
            self.object, limit=20
        )

        return context


# ==================== VISTAS DE MOVIMIENTO ====================

class MovimientoListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para listar movimientos de inventario.

    Permisos: bodega.view_movimiento
    """
    model = Movimiento
    template_name = 'bodega/movimiento/lista.html'
    context_object_name = 'movimientos'
    permission_required = 'bodega.view_movimiento'
    paginate_by = 50

    def get_queryset(self) -> QuerySet:
        """Retorna movimientos con relaciones optimizadas."""
        queryset = super().get_queryset().filter(
            eliminado=False
        ).select_related(
            'articulo', 'tipo', 'usuario'
        )

        # Filtros opcionales
        operacion = self.request.GET.get('operacion', '')
        tipo_id = self.request.GET.get('tipo', '')
        articulo_id = self.request.GET.get('articulo', '')

        if operacion:
            queryset = queryset.filter(operacion=operacion)

        if tipo_id:
            queryset = queryset.filter(tipo_id=tipo_id)

        if articulo_id:
            queryset = queryset.filter(articulo_id=articulo_id)

        return queryset.order_by('-fecha_creacion')

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Movimientos de Inventario'
        context['tipos'] = TipoMovimiento.objects.filter(activo=True, eliminado=False)
        context['operacion'] = self.request.GET.get('operacion', '')
        context['tipo_id'] = self.request.GET.get('tipo', '')
        return context


class MovimientoCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """
    Vista para crear un nuevo movimiento de inventario.

    Permisos: bodega.add_movimiento
    Auditoría: Registra acción CREAR automáticamente
    Transacción atómica: Garantiza que la creación del movimiento
    y actualización del stock se realicen de forma atómica
    Delega lógica de negocio a MovimientoService
    """
    model = Movimiento
    form_class = MovimientoForm
    template_name = 'bodega/movimiento/form.html'
    permission_required = 'bodega.add_movimiento'
    success_url = reverse_lazy('bodega:movimiento_lista')

    # Configuración de auditoría
    audit_action = 'CREAR'
    success_message = 'Movimiento registrado exitosamente. Stock actualizado: {obj.stock_despues}'

    def form_valid(self, form):
        """
        Procesa el formulario válido usando MovimientoService.

        El servicio maneja toda la lógica de negocio:
        - Validaciones de stock
        - Actualización atómica
        - Cálculo de stocks
        """
        try:
            # Delegar a MovimientoService
            service = MovimientoService()
            movimiento = service.registrar_movimiento(
                articulo=form.cleaned_data['articulo'],
                tipo=form.cleaned_data['tipo'],
                cantidad=form.cleaned_data['cantidad'],
                operacion=form.cleaned_data['operacion'],
                usuario=self.request.user,
                motivo=form.cleaned_data['motivo']
            )

            self.object = movimiento

            # Continuar con el flujo normal (mensaje y redirección)
            response = super().form_valid(form)
            self.log_action(self.object, self.request)
            return response

        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Registrar Movimiento'
        return context


class MovimientoDetailView(BaseAuditedViewMixin, DetailView):
    """
    Vista para ver el detalle de un movimiento.

    Permisos: bodega.view_movimiento
    """
    model = Movimiento
    template_name = 'bodega/movimiento/detalle.html'
    context_object_name = 'movimiento'
    permission_required = 'bodega.view_movimiento'

    def get_queryset(self) -> QuerySet:
        """Optimiza consultas con select_related."""
        return super().get_queryset().select_related(
            'articulo', 'tipo', 'usuario'
        ).filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Detalle de Movimiento'
        return context


# ==================== VISTAS DE ENTREGA DE ARTÍCULOS ====================

class EntregaArticuloListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para listar entregas de artículos con paginación y filtros.

    Permisos: bodega.view_entregaarticulo
    """
    model = EntregaArticulo
    template_name = 'bodega/entrega_articulo/lista.html'
    context_object_name = 'entregas'
    permission_required = 'bodega.view_entregaarticulo'
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        """Retorna entregas con relaciones optimizadas."""
        queryset = super().get_queryset().filter(
            eliminado=False
        ).select_related(
            'tipo', 'estado', 'entregado_por', 'bodega_origen'
        ).prefetch_related('detalles__articulo')

        # Filtros opcionales
        q = self.request.GET.get('q', '').strip()
        estado_id = self.request.GET.get('estado', '')
        bodega_id = self.request.GET.get('bodega', '')

        if q:
            queryset = queryset.filter(
                Q(numero__icontains=q) |
                Q(recibido_por__first_name__icontains=q) |
                Q(recibido_por__last_name__icontains=q) |
                Q(recibido_por__username__icontains=q)
            )

        if estado_id:
            queryset = queryset.filter(estado_id=estado_id)

        if bodega_id:
            queryset = queryset.filter(bodega_origen_id=bodega_id)

        return queryset.order_by('-fecha_entrega')

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Entregas de Artículos'
        context['estados'] = EstadoEntrega.objects.filter(activo=True, eliminado=False)
        context['bodegas'] = Bodega.objects.filter(activo=True, eliminado=False)
        return context


class EntregaArticuloCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """
    Vista para crear una nueva entrega de artículos.

    Permisos: bodega.add_entregaarticulo
    Auditoría: Registra acción CREAR automáticamente
    Delega lógica de negocio a EntregaArticuloService
    """
    model = EntregaArticulo
    form_class = EntregaArticuloForm
    template_name = 'bodega/entrega_articulo/form.html'
    permission_required = 'bodega.add_entregaarticulo'
    success_url = reverse_lazy('bodega:entrega_articulo_lista')

    # Configuración de auditoría
    audit_action = 'CREAR'
    success_message = 'Entrega {obj.numero} registrada exitosamente.'

    def form_valid(self, form):
        """
        Procesa el formulario válido usando EntregaArticuloService.

        El servicio maneja toda la lógica de negocio:
        - Generación de número de entrega
        - Validaciones de stock
        - Actualización atómica de stock
        - Registro de movimientos
        - Actualización de cantidades despachadas en solicitudes
        """
        try:
            # Validar que el usuario esté autenticado
            if not self.request.user or not self.request.user.is_authenticated:
                messages.error(self.request, 'Debe estar autenticado para registrar una entrega.')
                return self.form_invalid(form)

            # Obtener detalles del request (deben ser enviados vía POST)
            import json
            detalles_json = self.request.POST.get('detalles', '[]')
            detalles = json.loads(detalles_json)

            if not detalles:
                messages.error(
                    self.request,
                    'Debe agregar al menos un artículo a la entrega.'
                )
                return self.form_invalid(form)

            # Obtener usuario actual (puede ser de request o de middleware)
            from apps.accounts.middleware import get_current_user
            usuario_actual = self.request.user
            if not usuario_actual or not usuario_actual.is_authenticated:
                usuario_actual = get_current_user()

            if not usuario_actual or not usuario_actual.is_authenticated:
                messages.error(self.request, 'No se pudo identificar el usuario actual.')
                return self.form_invalid(form)

            # Delegar a EntregaArticuloService
            service = EntregaArticuloService()
            entrega = service.crear_entrega(
                bodega_origen=form.cleaned_data['bodega_origen'],
                tipo=form.cleaned_data['tipo'],
                entregado_por=usuario_actual,
                recibido_por=form.cleaned_data['recibido_por'],
                motivo=form.cleaned_data['motivo'],
                detalles=detalles,
                departamento_destino=form.cleaned_data.get('departamento_destino'),
                observaciones=form.cleaned_data.get('observaciones'),
                solicitud=form.cleaned_data.get('solicitud')
            )

            self.object = entrega

            # Actualizar estado de solicitud asociada a "Despachada"
            if self.object.solicitud:
                from apps.solicitudes.models import EstadoSolicitud
                try:
                    estado_despachada = EstadoSolicitud.objects.get(codigo='DESPACHADA', activo=True)
                    if self.object.solicitud.estado.codigo != 'DESPACHADA':
                        self.object.solicitud.estado = estado_despachada
                        self.object.solicitud.save()
                        print(f"DEBUG: Solicitud {self.object.solicitud.numero} actualizada a estado 'Despachada'")
                except EstadoSolicitud.DoesNotExist:
                    print("ERROR: No se encontró el estado 'DESPACHADA' para solicitudes")

            # Continuar con el flujo normal (mensaje y redirección)
            response = super().form_valid(form)
            self.log_action(self.object, self.request)
            return response

        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Registrar Entrega de Artículos'
        # Artículos disponibles para entrega
        context['articulos'] = Articulo.objects.filter(
            activo=True,
            eliminado=False
        ).select_related('categoria', 'unidad_medida').order_by('codigo')
        return context


class EntregaArticuloDetailView(BaseAuditedViewMixin, DetailView):
    """
    Vista para ver el detalle de una entrega de artículos.

    Permisos: bodega.view_entregaarticulo
    """
    model = EntregaArticulo
    template_name = 'bodega/entrega_articulo/detalle.html'
    context_object_name = 'entrega'
    permission_required = 'bodega.view_entregaarticulo'

    def get_queryset(self) -> QuerySet:
        """Optimiza consultas con select_related y prefetch_related."""
        return super().get_queryset().select_related(
            'tipo', 'estado', 'entregado_por', 'bodega_origen'
        ).prefetch_related(
            'detalles__articulo__categoria'
        ).filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Detalle Entrega {self.object.numero}'
        context['detalles'] = self.object.detalles.filter(eliminado=False)
        return context


# ==================== VISTAS DE ENTREGA DE BIENES ====================

class EntregaBienListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para listar entregas de bienes con paginación y filtros.

    Permisos: bodega.view_entregabien
    """
    model = EntregaBien
    template_name = 'bodega/entrega_bien/lista.html'
    context_object_name = 'entregas'
    permission_required = 'bodega.view_entregabien'
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        """Retorna entregas con relaciones optimizadas."""
        queryset = super().get_queryset().filter(
            eliminado=False
        ).select_related(
            'tipo', 'estado', 'entregado_por'
        ).prefetch_related('detalles__equipo')

        # Filtros opcionales
        q = self.request.GET.get('q', '').strip()
        estado_id = self.request.GET.get('estado', '')

        if q:
            queryset = queryset.filter(
                Q(numero__icontains=q) |
                Q(recibido_por__first_name__icontains=q) |
                Q(recibido_por__last_name__icontains=q) |
                Q(recibido_por__username__icontains=q)
            )

        if estado_id:
            queryset = queryset.filter(estado_id=estado_id)

        return queryset.order_by('-fecha_entrega')

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Entregas de Bienes/Activos'
        context['estados'] = EstadoEntrega.objects.filter(activo=True, eliminado=False)
        return context


class EntregaBienCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """
    Vista para crear una nueva entrega de bienes.

    Permisos: bodega.add_entregabien
    Auditoría: Registra acción CREAR automáticamente
    Delega lógica de negocio a EntregaBienService
    """
    model = EntregaBien
    form_class = EntregaBienForm
    template_name = 'bodega/entrega_bien/form.html'
    permission_required = 'bodega.add_entregabien'
    success_url = reverse_lazy('bodega:entrega_bien_lista')

    # Configuración de auditoría
    audit_action = 'CREAR'
    success_message = 'Entrega {obj.numero} registrada exitosamente.'

    def form_valid(self, form):
        """
        Procesa el formulario válido usando EntregaBienService.

        El servicio maneja toda la lógica de negocio:
        - Generación de número de entrega
        - Validaciones de bienes
        - Creación atómica de entrega con detalles
        """
        try:
            # Validar que el usuario esté autenticado
            if not self.request.user or not self.request.user.is_authenticated:
                messages.error(self.request, 'Debe estar autenticado para registrar una entrega.')
                return self.form_invalid(form)

            # Obtener detalles del request (deben ser enviados vía POST)
            import json
            detalles_json = self.request.POST.get('detalles', '[]')
            detalles = json.loads(detalles_json)

            if not detalles:
                messages.error(
                    self.request,
                    'Debe agregar al menos un bien a la entrega.'
                )
                return self.form_invalid(form)

            # Obtener usuario actual (puede ser de request o de middleware)
            from apps.accounts.middleware import get_current_user
            usuario_actual = self.request.user
            if not usuario_actual or not usuario_actual.is_authenticated:
                usuario_actual = get_current_user()

            if not usuario_actual or not usuario_actual.is_authenticated:
                messages.error(self.request, 'No se pudo identificar el usuario actual.')
                return self.form_invalid(form)

            # Delegar a EntregaBienService
            service = EntregaBienService()
            entrega = service.crear_entrega(
                tipo=form.cleaned_data['tipo'],
                entregado_por=usuario_actual,
                recibido_por=form.cleaned_data['recibido_por'],
                motivo=form.cleaned_data['motivo'],
                detalles=detalles,
                departamento_destino=form.cleaned_data.get('departamento_destino'),
                observaciones=form.cleaned_data.get('observaciones'),
                solicitud=form.cleaned_data.get('solicitud')
            )

            self.object = entrega

            # Actualizar estado de solicitud asociada a "Despachada"
            if self.object.solicitud:
                from apps.solicitudes.models import EstadoSolicitud
                try:
                    estado_despachada = EstadoSolicitud.objects.get(codigo='DESPACHADA', activo=True)
                    if self.object.solicitud.estado.codigo != 'DESPACHADA':
                        self.object.solicitud.estado = estado_despachada
                        self.object.solicitud.save()
                        print(f"DEBUG: Solicitud {self.object.solicitud.numero} actualizada a estado 'Despachada'")
                except EstadoSolicitud.DoesNotExist:
                    print("ERROR: No se encontró el estado 'DESPACHADA' para solicitudes")

            # Continuar con el flujo normal (mensaje y redirección)
            response = super().form_valid(form)
            self.log_action(self.object, self.request)
            return response

        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Registrar Entrega de Bienes/Activos'
        # Activos disponibles para entrega
        from apps.activos.models import Activo
        context['activos'] = Activo.objects.filter(
            activo=True,
            eliminado=False
        ).select_related('categoria', 'estado').order_by('nombre')
        return context


class EntregaBienDetailView(BaseAuditedViewMixin, DetailView):
    """
    Vista para ver el detalle de una entrega de bienes.

    Permisos: bodega.view_entregabien
    """
    model = EntregaBien
    template_name = 'bodega/entrega_bien/detalle.html'
    context_object_name = 'entrega'
    permission_required = 'bodega.view_entregabien'

    def get_queryset(self) -> QuerySet:
        """Optimiza consultas con select_related y prefetch_related."""
        return super().get_queryset().select_related(
            'tipo', 'estado', 'entregado_por'
        ).prefetch_related(
            'detalles__equipo__tipo_equipo'
        ).filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Detalle Entrega {self.object.numero}'
        context['detalles'] = self.object.detalles.filter(eliminado=False)
        return context


# ==================== ENDPOINTS AJAX ====================

@login_required
@require_http_methods(["GET"])
def obtener_articulos_solicitud(request, solicitud_id):
    """
    Endpoint AJAX para obtener los artículos de una solicitud.

    Retorna los artículos con cantidades solicitadas, aprobadas y despachadas.
    Permite al usuario ver qué artículos puede entregar y en qué cantidades.
    """
    try:
        from apps.solicitudes.models import Solicitud, DetalleSolicitud

        solicitud = Solicitud.objects.prefetch_related(
            'detalles__articulo__categoria'
        ).get(id=solicitud_id, tipo='ARTICULO', eliminado=False)

        articulos_data = []
        for detalle in solicitud.detalles.filter(eliminado=False):
            if detalle.articulo:  # Solo artículos (no activos)
                # Calcular cantidad pendiente de despacho
                cantidad_pendiente = float(detalle.cantidad_aprobada - detalle.cantidad_despachada)

                # Mostrar TODOS los artículos, no solo los pendientes
                # Obtener unidad de medida (ForeignKey)
                unidad_medida = detalle.articulo.unidad_medida.simbolo if detalle.articulo.unidad_medida else 'unidad'

                articulos_data.append({
                    'detalle_solicitud_id': detalle.id,
                    'articulo_id': detalle.articulo.id,
                    'articulo_codigo': detalle.articulo.codigo,
                    'articulo_nombre': detalle.articulo.nombre,
                    'categoria': detalle.articulo.categoria.nombre,
                    'unidad_medida': unidad_medida,  # Campo esperado por JavaScript
                    'stock_actual': int(detalle.articulo.stock_actual),
                    'cantidad_solicitada': int(detalle.cantidad_solicitada),
                    'cantidad_aprobada': int(detalle.cantidad_aprobada),
                    'cantidad_despachada': int(detalle.cantidad_despachada),
                    'cantidad_pendiente': cantidad_pendiente,
                    'observaciones': detalle.observaciones or ''
                })

        return JsonResponse({
            'success': True,
            'solicitud': {
                'numero': solicitud.numero,
                'solicitante': solicitud.solicitante.get_full_name() or solicitud.solicitante.username,
                'departamento': solicitud.departamento.nombre if solicitud.departamento else solicitud.area_solicitante,
                'motivo': solicitud.motivo,
                'bodega_origen_id': solicitud.bodega_origen.id if solicitud.bodega_origen else None
            },
            'articulos': articulos_data
        })

    except Solicitud.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Solicitud no encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def obtener_bienes_solicitud(request, solicitud_id):
    """
    Endpoint AJAX para obtener los bienes/activos de una solicitud.

    Retorna los bienes con cantidades solicitadas, aprobadas y despachadas.
    Permite al usuario ver qué bienes puede entregar y en qué cantidades.
    """
    try:
        from apps.solicitudes.models import Solicitud, DetalleSolicitud

        solicitud = Solicitud.objects.prefetch_related(
            'detalles__activo__categoria'
        ).get(id=solicitud_id, tipo='ACTIVO', eliminado=False)

        bienes_data = []
        for detalle in solicitud.detalles.filter(eliminado=False):
            if detalle.activo:  # Solo activos (no artículos)
                # Calcular cantidad pendiente de despacho
                cantidad_pendiente = int(detalle.cantidad_aprobada - detalle.cantidad_despachada)

                # Mostrar TODOS los bienes, no solo los pendientes
                bienes_data.append({
                    'detalle_solicitud_id': detalle.id,
                    'activo_id': detalle.activo.id,
                    'activo_codigo': detalle.activo.codigo,
                    'activo_nombre': detalle.activo.nombre,
                    'categoria': detalle.activo.categoria.nombre if detalle.activo.categoria else '-',
                    'cantidad_solicitada': int(detalle.cantidad_solicitada),
                    'cantidad_aprobada': int(detalle.cantidad_aprobada),
                    'cantidad_despachada': int(detalle.cantidad_despachada),
                    'cantidad_pendiente': cantidad_pendiente,
                    'observaciones': detalle.observaciones or ''
                })

        return JsonResponse({
            'success': True,
            'solicitud': {
                'numero': solicitud.numero,
                'solicitante': solicitud.solicitante.get_full_name() or solicitud.solicitante.username,
                'departamento': solicitud.departamento.nombre if solicitud.departamento else solicitud.area_solicitante,
                'motivo': solicitud.motivo
            },
            'bienes': bienes_data
        })

    except Solicitud.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Solicitud no encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== VISTAS MANTENEDORES: MARCA ====================


class MarcaListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para listar marcas de artículos.

    Permisos: bodega.view_marca
    Utiliza: MarcaRepository para acceso a datos optimizado
    """
    model = Marca
    template_name = 'bodega/mantenedores/marca/lista.html'
    context_object_name = 'marcas'
    permission_required = 'bodega.view_marca'
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        """Retorna marcas usando repository."""
        repo = MarcaRepository()

        # Filtrar solo no eliminados
        queryset = Marca.objects.filter(eliminado=False).order_by('codigo')

        # Búsqueda por query string
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(codigo__icontains=query) |
                Q(nombre__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Marcas'
        context['puede_crear'] = self.request.user.has_perm('bodega.add_marca')
        context['query'] = self.request.GET.get('q', '')
        return context


class MarcaCreateView(BaseAuditedViewMixin, CreateView):
    """
    Vista para crear una nueva marca.

    Permisos: bodega.add_marca
    Auditoría: Registra acción CREAR automáticamente
    """
    model = Marca
    form_class = MarcaForm
    template_name = 'bodega/mantenedores/marca/form.html'
    permission_required = 'bodega.add_marca'
    success_url = reverse_lazy('bodega:marca_lista')

    # Configuración de auditoría
    audit_action = 'CREAR'
    audit_description_template = 'Creó marca {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Marca {obj.nombre} creada exitosamente.'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Marca'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message(self.object))
        self.log_action(self.object, self.request)
        return response


class MarcaUpdateView(BaseAuditedViewMixin, UpdateView):
    """
    Vista para editar una marca existente.

    Permisos: bodega.change_marca
    Auditoría: Registra acción EDITAR automáticamente
    """
    model = Marca
    form_class = MarcaForm
    template_name = 'bodega/mantenedores/marca/form.html'
    permission_required = 'bodega.change_marca'
    success_url = reverse_lazy('bodega:marca_lista')

    # Configuración de auditoría
    audit_action = 'EDITAR'
    audit_description_template = 'Editó marca {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Marca {obj.nombre} actualizada exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite editar marcas no eliminadas."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Marca: {self.object.nombre}'
        context['action'] = 'Actualizar'
        context['marca'] = self.object
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message(self.object))
        self.log_action(self.object, self.request)
        return response


class MarcaDeleteView(BaseAuditedViewMixin, DeleteView):
    """
    Vista para eliminar (soft delete) una marca.

    Permisos: bodega.delete_marca
    Auditoría: Registra acción ELIMINAR automáticamente
    """
    model = Marca
    template_name = 'bodega/mantenedores/marca/eliminar.html'
    permission_required = 'bodega.delete_marca'
    success_url = reverse_lazy('bodega:marca_lista')

    # Configuración de auditoría
    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó marca {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Marca {obj.nombre} eliminada exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite eliminar marcas no eliminadas."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Marca: {self.object.nombre}'
        context['marca'] = self.object

        # Verificar si hay artículos asociados
        context['tiene_articulos'] = self.object.articulos.filter(eliminado=False).exists()
        context['count_articulos'] = self.object.articulos.filter(eliminado=False).count()

        return context

    def delete(self, request, *args, **kwargs):
        """Elimina usando soft delete."""
        self.object = self.get_object()

        # Verificar si tiene artículos asociados
        if self.object.articulos.filter(eliminado=False).exists():
            messages.error(
                request,
                f'No se puede eliminar la marca "{self.object.nombre}" porque tiene artículos asociados. '
                'Desactívela en su lugar.'
            )
            return redirect('bodega:marca_lista')

        # Soft delete
        self.object.eliminado = True
        self.object.activo = False
        self.object.save()

        messages.success(request, self.get_success_message(self.object))
        self.log_action(self.object, request)

        return redirect(self.success_url)


# ==================== VISTAS MANTENEDORES: OPERACION ====================


class OperacionListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para listar operaciones de movimiento.

    Permisos: bodega.view_operacion
    Utiliza: OperacionRepository para acceso a datos optimizado
    """
    model = Operacion
    template_name = 'bodega/mantenedores/operacion/lista.html'
    context_object_name = 'operaciones'
    permission_required = 'bodega.view_operacion'
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        """Retorna operaciones usando repository."""
        repo = OperacionRepository()

        # Filtrar solo no eliminados
        queryset = Operacion.objects.filter(eliminado=False).order_by('codigo')

        # Búsqueda por query string
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(codigo__icontains=query) |
                Q(nombre__icontains=query)
            )

        # Filtro por tipo (ENTRADA/SALIDA)
        tipo_filtro = self.request.GET.get('tipo', '').strip()
        if tipo_filtro in ['ENTRADA', 'SALIDA']:
            queryset = queryset.filter(tipo=tipo_filtro)

        return queryset

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Operaciones de Movimiento'
        context['puede_crear'] = self.request.user.has_perm('bodega.add_operacion')
        context['query'] = self.request.GET.get('q', '')
        context['tipo_filtro'] = self.request.GET.get('tipo', '')
        return context


class OperacionCreateView(BaseAuditedViewMixin, CreateView):
    """
    Vista para crear una nueva operación.

    Permisos: bodega.add_operacion
    Auditoría: Registra acción CREAR automáticamente
    """
    model = Operacion
    form_class = OperacionForm
    template_name = 'bodega/mantenedores/operacion/form.html'
    permission_required = 'bodega.add_operacion'
    success_url = reverse_lazy('bodega:operacion_lista')

    # Configuración de auditoría
    audit_action = 'CREAR'
    audit_description_template = 'Creó operación {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Operación {obj.nombre} creada exitosamente.'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Operación'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message(self.object))
        self.log_action(self.object, self.request)
        return response


class OperacionUpdateView(BaseAuditedViewMixin, UpdateView):
    """
    Vista para editar una operación existente.

    Permisos: bodega.change_operacion
    Auditoría: Registra acción EDITAR automáticamente
    """
    model = Operacion
    form_class = OperacionForm
    template_name = 'bodega/mantenedores/operacion/form.html'
    permission_required = 'bodega.change_operacion'
    success_url = reverse_lazy('bodega:operacion_lista')

    # Configuración de auditoría
    audit_action = 'EDITAR'
    audit_description_template = 'Editó operación {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Operación {obj.nombre} actualizada exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite editar operaciones no eliminadas."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Operación: {self.object.nombre}'
        context['action'] = 'Actualizar'
        context['operacion'] = self.object
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message(self.object))
        self.log_action(self.object, self.request)
        return response


class OperacionDeleteView(BaseAuditedViewMixin, DeleteView):
    """
    Vista para eliminar (soft delete) una operación.

    Permisos: bodega.delete_operacion
    Auditoría: Registra acción ELIMINAR automáticamente
    """
    model = Operacion
    template_name = 'bodega/mantenedores/operacion/eliminar.html'
    permission_required = 'bodega.delete_operacion'
    success_url = reverse_lazy('bodega:operacion_lista')

    # Configuración de auditoría
    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó operación {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Operación {obj.nombre} eliminada exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite eliminar operaciones no eliminadas."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Operación: {self.object.nombre}'
        context['operacion'] = self.object

        # Verificar si hay movimientos asociados
        context['tiene_movimientos'] = self.object.movimientos.filter(eliminado=False).exists()
        context['count_movimientos'] = self.object.movimientos.filter(eliminado=False).count()

        return context

    def delete(self, request, *args, **kwargs):
        """Elimina usando soft delete."""
        self.object = self.get_object()

        # Verificar si tiene movimientos asociados
        if self.object.movimientos.filter(eliminado=False).exists():
            messages.error(
                request,
                f'No se puede eliminar la operación "{self.object.nombre}" porque tiene movimientos asociados. '
                'Desactívela en su lugar.'
            )
            return redirect('bodega:operacion_lista')

        # Soft delete
        self.object.eliminado = True
        self.object.activo = False
        self.object.save()

        messages.success(request, self.get_success_message(self.object))
        self.log_action(self.object, request)

        return redirect(self.success_url)


# ==================== VISTAS MANTENEDORES: TIPOS DE MOVIMIENTO ====================


class TipoMovimientoListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para listar tipos de movimiento.

    Permisos: bodega.view_tipomovimiento
    Utiliza: TipoMovimientoRepository para acceso a datos optimizado
    """
    model = TipoMovimiento
    template_name = 'bodega/mantenedores/tipo_movimiento/lista.html'
    context_object_name = 'tipos'
    permission_required = 'bodega.view_tipomovimiento'
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        """Retorna tipos de movimiento usando repository."""
        from .repositories import TipoMovimientoRepository
        tipo_repo = TipoMovimientoRepository()

        # Incluir inactivos y eliminados para administración
        queryset = TipoMovimiento.objects.filter(eliminado=False).order_by('codigo')

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
        context['titulo'] = 'Tipos de Movimiento'
        context['puede_crear'] = self.request.user.has_perm('bodega.add_tipomovimiento')
        return context


class TipoMovimientoCreateView(BaseAuditedViewMixin, CreateView):
    """
    Vista para crear un nuevo tipo de movimiento.

    Permisos: bodega.add_tipomovimiento
    Auditoría: Registra acción CREAR automáticamente
    """
    model = TipoMovimiento
    form_class = TipoMovimientoForm
    template_name = 'bodega/mantenedores/tipo_movimiento/form.html'
    permission_required = 'bodega.add_tipomovimiento'
    success_url = reverse_lazy('bodega:tipo_movimiento_lista')

    # Configuración de auditoría
    audit_action = 'CREAR'
    audit_description_template = 'Creó tipo de movimiento {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Tipo de movimiento {obj.nombre} creado exitosamente.'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Tipo de Movimiento'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message(self.object))
        self.log_action(self.object, self.request)
        return response


class TipoMovimientoUpdateView(BaseAuditedViewMixin, UpdateView):
    """
    Vista para editar un tipo de movimiento existente.

    Permisos: bodega.change_tipomovimiento
    Auditoría: Registra acción EDITAR automáticamente
    """
    model = TipoMovimiento
    form_class = TipoMovimientoForm
    template_name = 'bodega/mantenedores/tipo_movimiento/form.html'
    permission_required = 'bodega.change_tipomovimiento'
    success_url = reverse_lazy('bodega:tipo_movimiento_lista')

    # Configuración de auditoría
    audit_action = 'EDITAR'
    audit_description_template = 'Editó tipo de movimiento {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Tipo de movimiento {obj.nombre} actualizado exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite editar tipos no eliminados."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Tipo de Movimiento: {self.object.nombre}'
        context['action'] = 'Actualizar'
        context['tipo'] = self.object
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message(self.object))
        self.log_action(self.object, self.request)
        return response


class TipoMovimientoDeleteView(BaseAuditedViewMixin, DeleteView):
    """
    Vista para eliminar (soft delete) un tipo de movimiento.

    Permisos: bodega.delete_tipomovimiento
    Auditoría: Registra acción ELIMINAR automáticamente
    """
    model = TipoMovimiento
    template_name = 'bodega/mantenedores/tipo_movimiento/eliminar.html'
    permission_required = 'bodega.delete_tipomovimiento'
    success_url = reverse_lazy('bodega:tipo_movimiento_lista')

    # Configuración de auditoría
    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó tipo de movimiento {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Tipo de movimiento {obj.nombre} eliminado exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite eliminar tipos no eliminados."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Tipo de Movimiento: {self.object.nombre}'
        context['tipo'] = self.object

        # Verificar si hay movimientos asociados
        context['tiene_movimientos'] = self.object.movimientos.filter(eliminado=False).exists()
        context['count_movimientos'] = self.object.movimientos.filter(eliminado=False).count()

        return context

    def delete(self, request, *args, **kwargs):
        """Elimina usando soft delete."""
        self.object = self.get_object()

        # Verificar si tiene movimientos asociados
        if self.object.movimientos.filter(eliminado=False).exists():
            messages.error(
                request,
                f'No se puede eliminar el tipo "{self.object.nombre}" porque tiene movimientos asociados. '
                'Desactívelo en su lugar.'
            )
            return redirect('bodega:tipo_movimiento_lista')

        # Soft delete
        self.object.eliminado = True
        self.object.activo = False
        self.object.save()

        messages.success(request, self.get_success_message(self.object))
        self.log_action(self.object, request)

        return redirect(self.success_url)


# ==================== IMPORTACION EXCEL PARA MANTENEDORES ====================


@login_required
def marca_descargar_plantilla(request):
    """Vista para descargar plantilla Excel de marcas."""
    contenido = ImportacionExcelService.generar_plantilla_marcas()
    
    response = HttpResponse(
        contenido,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="plantilla_marcas.xlsx"'
    return response


@login_required
def marca_importar_excel(request):
    """Vista para importar marcas desde Excel."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)
    
    if 'archivo' not in request.FILES:
        return JsonResponse({'error': 'No se proporciono archivo'}, status=400)
    
    archivo = request.FILES['archivo']
    
    # Validar archivo
    es_valido, mensaje_error = ImportacionExcelService.validar_archivo_excel(archivo)
    if not es_valido:
        return JsonResponse({'error': mensaje_error}, status=400)
    
    try:
        creadas, actualizadas, errores = ImportacionExcelService.importar_marcas(archivo, request.user)
        
        mensaje = f"Importacion completada: {creadas} marcas creadas, {actualizadas} actualizadas"
        if errores:
            mensaje += f". Errores: {len(errores)}"
        
        return JsonResponse({
            'success': True,
            'mensaje': mensaje,
            'creadas': creadas,
            'actualizadas': actualizadas,
            'errores': errores[:10]  # Limitar a 10 errores
        })
    except Exception as e:
        return JsonResponse({'error': f'Error al importar: {str(e)}'}, status=500)


# Operaciones
@login_required
def operacion_descargar_plantilla(request):
    """Vista para descargar plantilla Excel de operaciones."""
    contenido = ImportacionExcelService.generar_plantilla_operaciones()
    response = HttpResponse(contenido, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="plantilla_operaciones.xlsx"'
    return response


@login_required
def operacion_importar_excel(request):
    """Vista para importar operaciones desde Excel."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)
    if 'archivo' not in request.FILES:
        return JsonResponse({'error': 'No se proporciono archivo'}, status=400)
    archivo = request.FILES['archivo']
    es_valido, mensaje_error = ImportacionExcelService.validar_archivo_excel(archivo)
    if not es_valido:
        return JsonResponse({'error': mensaje_error}, status=400)
    try:
        creadas, actualizadas, errores = ImportacionExcelService.importar_operaciones(archivo, request.user)
        mensaje = f"Importacion completada: {creadas} operaciones creadas, {actualizadas} actualizadas"
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


# Tipos de Movimiento
@login_required
def tipo_movimiento_descargar_plantilla(request):
    """Vista para descargar plantilla Excel de tipos de movimiento."""
    contenido = ImportacionExcelService.generar_plantilla_tipos_movimiento()
    response = HttpResponse(contenido, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="plantilla_tipos_movimiento.xlsx"'
    return response


@login_required
def tipo_movimiento_importar_excel(request):
    """Vista para importar tipos de movimiento desde Excel."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)
    if 'archivo' not in request.FILES:
        return JsonResponse({'error': 'No se proporciono archivo'}, status=400)
    archivo = request.FILES['archivo']
    es_valido, mensaje_error = ImportacionExcelService.validar_archivo_excel(archivo)
    if not es_valido:
        return JsonResponse({'error': mensaje_error}, status=400)
    try:
        creadas, actualizadas, errores = ImportacionExcelService.importar_tipos_movimiento(archivo, request.user)
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
