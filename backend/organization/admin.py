from django.contrib import admin
from .models import Facultad, Departamento, PerfilUsuario

admin.site.register(Facultad)
admin.site.register(Departamento)
admin.site.register(PerfilUsuario)