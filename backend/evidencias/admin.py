from django.contrib import admin
from .models import Evidencia


@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'asignacion', 'subido_por', 'version', 'tamano', 'fecha_subida']
    list_filter = ['tipo_archivo', 'fecha_subida']
    search_fields = ['nombre', 'descripcion']
