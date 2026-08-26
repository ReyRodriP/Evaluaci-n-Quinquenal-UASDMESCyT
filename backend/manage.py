#!/usr/bin/env python
"""
@file manage.py
@brief Script de administración de Django.
@details Utilidad de línea de comandos para tareas administrativas
del proyecto Evaluación Quinquenal, incluyendo migraciones,
creación de superusuarios y otros comandos de gestión.
"""
import os
import sys


def main():
    """@brief Ejecuta las tareas administrativas de Django.
    @return None
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluacionQuinquenal.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
