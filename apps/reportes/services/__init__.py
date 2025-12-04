"""
Servicios de reporteria.
Cada servicio recibe filtros y retorna un ReportResult (DTO).
Sin acceso directo a ORM ni renderizado (SRP).
"""

from .reporte import ReporteService

__all__ = ['ReporteService']
