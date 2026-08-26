"""
@file wsgi.py
@brief Configuración WSGI del proyecto Evaluación Quinquenal.
@details Expone el callable WSGI como variable de módulo ``application``.
Para más información sobre este archivo, consulte:
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluacionQuinquenal.settings')

application = get_wsgi_application()
