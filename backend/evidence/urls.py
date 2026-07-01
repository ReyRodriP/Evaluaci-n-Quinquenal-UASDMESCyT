from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EvidenciaViewSet, VersionEvidenciaViewSet

router = DefaultRouter()
router.register(r'evidencias', EvidenciaViewSet)
router.register(r'versiones', VersionEvidenciaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]