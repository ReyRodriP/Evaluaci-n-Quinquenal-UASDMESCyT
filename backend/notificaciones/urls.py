"""
@file urls.py
@brief URLs de la app de notificaciones.
@details Define las rutas URL para los endpoints de notificaciones
del sistema.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificacionViewSet

router = DefaultRouter()
router.register(r'notificaciones', NotificacionViewSet, basename='notificacion')

urlpatterns = [
    path('', include(router.urls)),
]
