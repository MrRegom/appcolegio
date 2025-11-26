from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class CommonFilters:
    """
    Filtros comunes para reportes.
    SRP: solo validación/estructura de filtros, sin lógica de negocio.
    """

    desde: date
    hasta: date
    bodega_id: Optional[int] = None
    categoria_id: Optional[int] = None
    proveedor_id: Optional[int] = None


def validate_dates(desde: date, hasta: date) -> None:
    """Valida coherencia de rango de fechas."""
    if desde > hasta:
        raise ValueError("La fecha 'desde' no puede ser mayor que 'hasta'.")


