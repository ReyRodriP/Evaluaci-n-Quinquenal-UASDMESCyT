from django.contrib import admin
from .models import Auditoria


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ['accion', 'usuario', 'modelo', 'fecha']
    list_filter = ['accion', 'modelo', 'fecha']
    search_fields = ['accion', 'modelo', 'descripcion']
    readonly_fields = ['usuario', 'accion', 'modelo', 'registro_id', 'descripcion', 'fecha']
