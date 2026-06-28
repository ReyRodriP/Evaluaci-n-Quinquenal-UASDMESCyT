from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'roles', views.GroupViewSet)
router.register(r'permisos', views.PermissionViewSet)

urlpatterns = [
    re_path('login', views.login),
    re_path('register', views.register),
    re_path('me', views.me),
    re_path('profile', views.profile),
    re_path('change_password', views.change_password),
    path('', include(router.urls)),
]