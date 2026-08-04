from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'roles', views.GroupViewSet)
router.register(r'permisos', views.PermissionViewSet)
router.register(r'usuarios', views.UserViewSet)

urlpatterns = [
    re_path('login', views.login),
    re_path('register', views.register),
    re_path('logout', views.logout),
    re_path('me', views.me),
    re_path('profile', views.profile),
    re_path('change_password', views.change_password),
    re_path('forgot_password', views.forgot_password),
    re_path('reset_password', views.reset_password),
    path('', include(router.urls)),
]