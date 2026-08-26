"""
@file urls.py
@brief URLs de la app de búsqueda.
@details Define las rutas URL para el endpoint de búsqueda global.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("search/", views.search, name="search"),
]
