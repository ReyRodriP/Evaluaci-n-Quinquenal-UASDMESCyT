"""
@file asgi.py
@brief Configuración ASGI del proyecto Evaluación Quinquenal.
@details Expone el callable ASGI como variable de módulo ``application``.
Para más información sobre este archivo, consulte:
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "evaluacionQuinquenal.settings")

application = get_asgi_application()
