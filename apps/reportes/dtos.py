from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ReportResult:
    """
    DTO genérico para transportar resultados de reportería entre capas.
    Mantiene SRP: no conoce de ORM ni de renderizado.
    """

    title: str
    columns: List[str]
    rows: List[List[Any]]
    totals: Optional[Dict[str, Any]] = None
    filters_summary: Optional[Dict[str, Any]] = None


