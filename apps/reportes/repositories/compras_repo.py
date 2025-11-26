from typing import Iterable, Optional
from django.db.models import F, Q
from django.utils.timezone import now
from apps.compras.models import OrdenCompra


def oc_atrasadas(
    hoy=None,
    proveedor_id: Optional[int] = None,
    bodega_id: Optional[int] = None,
) -> Iterable[OrdenCompra]:
    """
    Devuelve órdenes de compra atrasadas respecto a su fecha comprometida.
    Criterio:
      - Sin fecha_entrega_real y fecha_entrega_esperada < hoy
      - Con fecha_entrega_real > fecha_entrega_esperada
    SRP: solo filtra/ordena y retorna queryset.
    """
    if hoy is None:
        hoy = now().date()

    qs = OrdenCompra.objects.select_related("proveedor", "bodega_destino").filter(
        eliminado=False
    ).filter(
        Q(fecha_entrega_real__isnull=True, fecha_entrega_esperada__lt=hoy)
        | Q(fecha_entrega_real__gt=F("fecha_entrega_esperada"))
    )

    if proveedor_id:
        qs = qs.filter(proveedor_id=proveedor_id)
    if bodega_id:
        qs = qs.filter(bodega_destino_id=bodega_id)

    return qs.order_by("proveedor__razon_social", "numero")


