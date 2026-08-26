"""
@file urls.py
@brief Configuracion de URLs para la app de cuentas de usuario
@details Define las rutas de acceso para autenticacion, gestion de usuarios,
roles, permisos y operaciones de perfil.
"""

from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"roles", views.GroupViewSet)
router.register(r"permisos", views.PermissionViewSet)
router.register(r"usuarios", views.UserViewSet)

urlpatterns = [
    re_path(r"^login$", views.login),
    re_path(r"^register$", views.register),
    re_path(r"^logout$", views.logout),
    re_path(r"^me$", views.me),
    re_path(r"^profile$", views.profile),
    re_path(r"^change_password$", views.change_password),
    re_path(r"^forgot_password$", views.forgot_password),
    re_path(r"^reset_password$", views.reset_password),
    path("", include(router.urls)),
]
