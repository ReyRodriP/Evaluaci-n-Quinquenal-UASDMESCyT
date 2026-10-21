from django.contrib import admin

from .models import AmbitoEvaluacion, AmbitoRevision, Departamento, Facultad, PerfilUsuario

admin.site.register(Facultad)
admin.site.register(Departamento)
admin.site.register(PerfilUsuario)
admin.site.register(AmbitoEvaluacion)


@admin.register(AmbitoRevision)
class AmbitoRevisionAdmin(admin.ModelAdmin):
    list_display = ["usuario", "unidad_organizacional", "periodo", "activo"]
    list_filter = ["activo", "periodo"]
    # Mantener validación de rol, auditoría y desactivación en la API de gestión.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
