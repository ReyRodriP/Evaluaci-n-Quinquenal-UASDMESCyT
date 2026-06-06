from django.urls import path, re_path
from . import views

urlpatterns = [
    re_path('login', views.login),
    re_path('register', views.register),
    re_path('me', views.me),
    re_path('profile', views.profile),
    re_path('change_password', views.change_password)
]