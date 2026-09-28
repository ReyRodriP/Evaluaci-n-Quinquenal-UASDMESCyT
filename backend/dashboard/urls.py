"""
@file urls.py
@brief URLs de la app de dashboard.
@details Define las rutas URL para los endpoints del panel de control.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/resumen/", views.resumen, name="dashboard-resumen"),
    path("dashboard/departamento/<int:pk>/", views.departamento_dashboard, name="dashboard-departamento"),
    path("dashboard/avance/", views.avance, name="dashboard-avance"),
    path("dashboard/periodo/<int:pk>/", views.periodo_dashboard, name="dashboard-periodo"),
]
