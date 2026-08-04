from django.contrib import admin
from .models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'usuario', 'leida', 'fecha_creacion']
    list_filter = ['leida', 'fecha_creacion']
    search_fields = ['titulo', 'mensaje', 'usuario__username']
