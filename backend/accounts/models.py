from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    foto_perfil = models.ImageField(
        upload_to='profile_pictures',
        blank=True,
        null=True
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    ) #Para los demas campos utilizaremos las herramientas de django como 