"""
@file urls.py
@brief URLs de la app de reportes.
@details Define las rutas URL para los endpoints de reportes
y exportación del sistema.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('reportes/general/', views.general, name='reporte-general'),
    path('reportes/general/exportar/', views.general_exportar, name='reporte-general-exportar'),
    path('reportes/facultad/<int:pk>/', views.por_facultad, name='reporte-facultad'),
    path('reportes/facultad/<int:pk>/exportar/', views.por_facultad_exportar, name='reporte-facultad-exportar'),
    path('reportes/departamento/<int:pk>/', views.por_departamento, name='reporte-departamento'),
    path('reportes/departamento/<int:pk>/exportar/', views.por_departamento_exportar, name='reporte-departamento-exportar'),
    path('reportes/evidencias/', views.evidencias, name='reporte-evidencias'),
    path('reportes/evidencias/exportar/', views.evidencias_exportar, name='reporte-evidencias-exportar'),
    path('reportes/observaciones/', views.observaciones, name='reporte-observaciones'),
    path('reportes/observaciones/exportar/', views.observaciones_exportar, name='reporte-observaciones-exportar'),
    path('reportes/auditoria/', views.auditoria, name='reporte-auditoria'),
    path('reportes/auditoria/exportar/', views.auditoria_exportar, name='reporte-auditoria-exportar'),
    path('reportes/usuarios/', views.usuarios, name='reporte-usuarios'),
    path('reportes/usuarios/exportar/', views.usuarios_exportar, name='reporte-usuarios-exportar'),
]
