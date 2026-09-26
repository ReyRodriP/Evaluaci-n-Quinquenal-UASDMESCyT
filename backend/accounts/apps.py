from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "accounts"

    def ready(self):
        from . import signals  # noqa: F401  (conecta proteccion y sincronizacion de permisos)
