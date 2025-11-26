from typing import List, Optional
from datetime import date
from django.db.models import Sum
from django.utils.timezone import now

from apps.reportes.dtos import ReportResult
from apps.reportes.repositories import compras_repo
from apps.compras.models import DetalleOrdenCompraArticulo, DetalleRecepcionArticulo


class OcAtrasadasPorProveedorService:
    """
    Servicio: Órdenes de compra atrasadas por proveedor.
    SRP: toma queryset del repository, calcula métricas y arma DTO.
    """

    def run(self, proveedor_id: Optional[int] = None, bodega_id: Optional[int] = None) -> ReportResult:
        hoy = now().date()
        ocs = compras_repo.oc_atrasadas(hoy=hoy, proveedor_id=proveedor_id, bodega_id=bodega_id)
        rows: List[List] = []

        for oc in ocs:
            ordenado = (
                DetalleOrdenCompraArticulo.objects.filter(eliminado=False, orden_compra=oc).aggregate(t=Sum("cantidad"))[
                    "t"
                ]
                or 0
            )
            recibido = (
                DetalleRecepcionArticulo.objects.filter(
                    eliminado=False, recepcion__orden_compra=oc
                ).aggregate(t=Sum("cantidad"))["t"]
                or 0
            )
            pct = round((recibido / ordenado) * 100, 2) if ordenado else 0

            if oc.fecha_entrega_real:
                dias_atraso = max((oc.fecha_entrega_real - oc.fecha_entrega_esperada).days, 0)
            else:
                dias_atraso = (hoy - oc.fecha_entrega_esperada).days

            if recibido == 0 and not oc.fecha_entrega_real:
                estado = "Sin recepción"
            elif recibido < ordenado and not oc.fecha_entrega_real:
                estado = "Parcial"
            else:
                estado = "Tardía"

            rows.append(
                [
                    oc.proveedor.rut if hasattr(oc.proveedor, "rut") else "",
                    oc.proveedor.razon_social,
                    oc.numero,
                    oc.fecha_orden.strftime("%d/%m/%Y") if oc.fecha_orden else "",
                    oc.fecha_entrega_esperada.strftime("%d/%m/%Y") if oc.fecha_entrega_esperada else "",
                    oc.fecha_entrega_real.strftime("%d/%m/%Y") if oc.fecha_entrega_real else "",
                    int(ordenado),
                    int(recibido),
                    pct,
                    dias_atraso,
                    estado,
                ]
            )

        return ReportResult(
            title="Órdenes de compra atrasadas por proveedor",
            columns=[
                "RUT",
                "Proveedor",
                "N° OC",
                "Fecha OC",
                "Fecha Comprometida",
                "Fecha Últ. Recepción",
                "Cant. Ordenada",
                "Cant. Recibida",
                "% Recibido",
                "Días de atraso",
                "Estado",
            ],
            rows=rows,
            filters_summary={"proveedor_id": proveedor_id, "bodega_id": bodega_id, "hoy": hoy.strftime("%d/%m/%Y")},
        )


