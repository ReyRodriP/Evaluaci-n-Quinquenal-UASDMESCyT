"""Rutas de la app de vinculación.

Montadas en /api/vinculacion/ desde evaluacionQuinquenal/urls.py.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ContextoCriterio, ContextoIndicador, CorrespondenciaViewSet

router = DefaultRouter()

router.register(r"correspondencias", CorrespondenciaViewSet)

urlpatterns = [
    path("contexto/criterio/<int:criterio_id>/", ContextoCriterio.as_view()),
    path("contexto/indicador/<int:indicador_id>/", ContextoIndicador.as_view()),
] + router.urls
