import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Crea o actualiza el superusuario por defecto"

    def add_arguments(self, parser):
        parser.add_argument("--username", default="mrPopoMaster")
        parser.add_argument("--email", default="popomrMaster001@gmail.com")
        parser.add_argument("--password", default="")

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]
        password = options["password"] or os.getenv("SUPERUSER_PASSWORD", "")

        if not password:
            self.stderr.write(
                self.style.ERROR("Debes indicar una contrasena con --password o la variable de entorno SUPERUSER_PASSWORD.")
            )
            raise SystemExit(1)

        if len(password) < 8:
            self.stderr.write(self.style.ERROR("La contrasena debe tener al menos 8 caracteres."))
            raise SystemExit(1)

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.email = email
        user.set_password(password)
        user.save()

        action = "creado" if created else "actualizado"
        self.stdout.write(self.style.SUCCESS(f"Superusuario '{username}' {action} correctamente."))