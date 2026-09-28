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
    path('password-reset/confirm', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset', views.password_reset_request, name='password_reset_request'),
    re_path('login', views.login),
    re_path('register', views.register),
    re_path('logout', views.logout),
    re_path('me', views.me),
    re_path('profile', views.profile),
    re_path('change_password', views.change_password),
    re_path('forgot_password', views.forgot_password),
    re_path('reset_password', views.reset_password),
    re_path(r'token/refresh/cookie', views.token_refresh_cookie),
    path('', include(router.urls)),
]
