"""
Helpers para trabajar con permisos categorizados del módulo de solicitudes.

Funciones auxiliares para consultar permisos organizados por módulo funcional.
"""

from typing import Optional
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet


def obtener_modulo_permiso(codename: str) -> Optional[str]:
    """
    Obtiene el módulo al que pertenece un permiso.

    Args:
        codename: Código del permiso (ej: 'aprobar_solicitudes')

    Returns:
        Nombre del módulo o None si no existe.

    Example:
        >>> obtener_modulo_permiso('aprobar_solicitudes')
        'Gestión'
    """
    from .models import CategoriaPermiso

    try:
        categoria = CategoriaPermiso.objects.select_related('permiso').get(
            permiso__codename=codename
        )
        return categoria.get_modulo_display()
    except CategoriaPermiso.DoesNotExist:
        return None


def obtener_permisos_por_modulo() -> dict[str, QuerySet[Permission]]:
    """
    Obtiene permisos del modelo Solicitud organizados por módulo.

    Returns:
        Diccionario con estructura:
        {
            'Gestión': QuerySet[Permission],
            'Solicitud Artículos': QuerySet[Permission],
            ...
        }

    Example:
        >>> permisos = obtener_permisos_por_modulo()
        >>> for modulo, qs in permisos.items():
        ...     print(f"{modulo}: {qs.count()} permisos")
    """
    from .models import CategoriaPermiso

    permisos_organizados = {}

    # Obtener categorías ordenadas
    categorias = CategoriaPermiso.objects.select_related(
        'permiso'
    ).order_by('modulo', 'orden')

    # Agrupar por módulo
    for categoria in categorias:
        modulo_nombre = categoria.get_modulo_display()

        if modulo_nombre not in permisos_organizados:
            permisos_organizados[modulo_nombre] = []

        permisos_organizados[modulo_nombre].append(categoria.permiso)

    return permisos_organizados


def enriquecer_permisos_con_modulo(permisos_queryset: QuerySet[Permission]) -> list[Permission]:
    """
    Agrega atributo 'modulo' a cada permiso del queryset.

    Args:
        permisos_queryset: QuerySet de Permission

    Returns:
        Lista de permisos con atributo 'modulo' agregado.

    Example:
        >>> permisos = Permission.objects.filter(content_type__app_label='solicitudes')
        >>> permisos_enriquecidos = enriquecer_permisos_con_modulo(permisos)
        >>> for p in permisos_enriquecidos:
        ...     print(f"{p.modulo} - {p.name}")
    """
    from .models import CategoriaPermiso

    permisos_lista = list(permisos_queryset)

    # Obtener categorías en una sola query
    codenames = [p.codename for p in permisos_lista]
    categorias_dict = {
        cat.permiso.codename: cat
        for cat in CategoriaPermiso.objects.filter(
            permiso__codename__in=codenames
        ).select_related('permiso')
    }

    # Agregar atributo modulo
    for permiso in permisos_lista:
        categoria = categorias_dict.get(permiso.codename)
        permiso.modulo = categoria.get_modulo_display() if categoria else None

    return permisos_lista


def obtener_permisos_solicitud() -> QuerySet[Permission]:
    """
    Obtiene todos los permisos del modelo Solicitud.

    Returns:
        QuerySet de Permission del modelo Solicitud.
    """
    from .models import Solicitud

    content_type = ContentType.objects.get_for_model(Solicitud)
    return Permission.objects.filter(content_type=content_type)
