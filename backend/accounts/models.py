"""
@file models.py
@brief Modelo de usuario personalizado para el sistema de evaluacion quinquenal UASD-MESCyT
@details Define el modelo Usuario extendiendo AbstractUser con campos adicionales como
telefono, foto de perfil y fecha de registro.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    @class Usuario
    @brief Modelo de usuario personalizado que extiende AbstractUser
    @details Agrega campos de telefono, foto de perfil y fecha de registro
    al modelo de usuario estandar de Django.
    """

    email = models.EmailField(max_length=254, unique=True)

    telefono = models.CharField(max_length=20, blank=True, null=True)
    foto_perfil = models.ImageField(upload_to="profile_pictures", blank=True, null=True)

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )  # Para los demas campos utilizaremos las herramientas de django como
