from typing import List
from datetime import date
from django.utils.timezone import now

from apps.reportes.dtos import ReportResult
from apps.reportes.repositories import bodega_repo


class ArticulosSinMovimientoService:
    """
    Servicio: Artículos sin movimiento en período.
    SRP: arma el dataset y totales desde repositories.
    """

    def run(self, desde: date, hasta: date, bodega_id=None, categoria_id=None) -> ReportResult:
        items = bodega_repo.articulos_sin_movimiento(desde, hasta, bodega_id, categoria_id)
        rows: List[List] = []
        hoy = now().date()

        for a in items:
            ultimo = a.ultimo_movimiento.date() if getattr(a, "ultimo_movimiento", None) else None
            dias_sin = (hoy - ultimo).days if ultimo else None
            rows.append(
                [
                    a.codigo,
                    a.nombre,
                    a.ubicacion_fisica.nombre if a.ubicacion_fisica_id else "",
                    a.categoria.nombre if a.categoria_id else "",
                    a.stock_actual,
                    a.stock_minimo or 0,
                    a.punto_reorden or "",
                    ultimo.strftime("%d/%m/%Y") if ultimo else "Sin registros",
                    dias_sin if dias_sin is not None else "",
                ]
            )

        return ReportResult(
            title="Artículos sin movimiento",
            columns=[
                "Código",
                "Nombre",
                "Bodega",
                "Categoría",
                "Stock",
                "Mínimo",
                "Pto. Pedido",
                "Último movimiento",
                "Días sin movimiento",
            ],
            rows=rows,
            filters_summary={
                "desde": desde.strftime("%d/%m/%Y"),
                "hasta": hasta.strftime("%d/%m/%Y"),
                "bodega_id": bodega_id,
                "categoria_id": categoria_id,
            },
        )


