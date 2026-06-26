from django.contrib import admin
from .models import Periodo, Criterio, Indicador, Asignacion


@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'fecha_inicio', 'fecha_fin', 'activo']
    list_filter = ['activo']


@admin.register(Criterio)
class CriterioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'periodo', 'activo']
    list_filter = ['activo', 'periodo']


@admin.register(Indicador)
class IndicadorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'criterio', 'obligatorio', 'activo']
    list_filter = ['obligatorio', 'activo', 'criterio']


@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):
    list_display = ['indicador', 'departamento', 'periodo', 'estado']
    list_filter = ['estado', 'periodo']
