"""
URLs para el módulo de inventario.

IMPORTANTE: Los modelos y vistas de este módulo fueron migrados a apps.activos
"""

from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # Menú principal de gestores
    path('', views.menu_gestores, name='menu_gestores'),
]

