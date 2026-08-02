from django.urls import path
from . import views

urlpatterns = [
    path('reportes/observaciones/', views.observaciones, name='reporte-observaciones'),
    path('reportes/observaciones/exportar/', views.observaciones_exportar, name='reporte-observaciones-exportar'),
    path('reportes/auditoria/', views.auditoria, name='reporte-auditoria'),
    path('reportes/auditoria/exportar/', views.auditoria_exportar, name='reporte-auditoria-exportar'),
    path('reportes/usuarios/', views.usuarios, name='reporte-usuarios'),
    path('reportes/usuarios/exportar/', views.usuarios_exportar, name='reporte-usuarios-exportar'),
]
