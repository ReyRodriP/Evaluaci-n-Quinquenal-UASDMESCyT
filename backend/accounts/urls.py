from django.urls import path, re_path
from . import views

urlpatterns = [
    re_path('login', views.login),
    re_path('register', views.register),
<<<<<<< HEAD
    re_path('logout', views.logout),
    re_path('me', views.me),
    re_path('profile', views.profile),
    re_path('change_password', views.change_password),
    re_path('forgot_password', views.forgot_password),
    re_path('reset_password', views.reset_password)
=======
    re_path('me', views.me),
    re_path('profile', views.profile),
    re_path('change_password', views.change_password)
>>>>>>> Jose-Manuel
]