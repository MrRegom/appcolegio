from typing import Iterable, Optional
from django.db.models import OuterRef, Subquery, Exists
from apps.bodega.models import Articulo, Movimiento


def articulos_sin_movimiento(
    desde,
    hasta,
    bodega_id: Optional[int] = None,
    categoria_id: Optional[int] = None,
) -> Iterable[Articulo]:
    """
    Devuelve artículos SIN movimientos en el período indicado.
    SRP: solo consulta/filtrado, sin cálculos de negocio.
    """
    qs = Articulo.objects.filter(eliminado=False)

    if bodega_id:
        qs = qs.filter(ubicacion_fisica_id=bodega_id)
    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)

    movs_rango = Movimiento.objects.filter(
        articulo_id=OuterRef("pk"),
        eliminado=False,
        fecha_creacion__date__gte=desde,
        fecha_creacion__date__lte=hasta,
    )

    # Anotar último movimiento histórico (para mostrar en el reporte)
    ultimo_mov_subq = (
        Movimiento.objects.filter(articulo_id=OuterRef("pk"), eliminado=False)
        .order_by("-fecha_creacion")
        .values("fecha_creacion")[:1]
    )

    # Usar Exists para detectar presencia de movimientos en el rango
    qs = qs.annotate(
        ultimo_movimiento=Subquery(ultimo_mov_subq),
        tiene_mov=Exists(movs_rango),
    ).filter(tiene_mov=False)

    return qs.order_by("codigo")



