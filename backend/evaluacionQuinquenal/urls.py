from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('organization.urls')),
    path('api/', include('evaluation.urls')),
    path('api/', include('accounts.urls')),
]
