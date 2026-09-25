from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Notificacion
from .utils import crear_notificacion

User = get_user_model()


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
class NotificacionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="notifuser", email="notif@test.com", password="testpass123")

    def test_crear(self):
        notif = Notificacion.objects.create(
            usuario=self.user, titulo="Nueva notificación", mensaje="Tienes una nueva tarea pendiente"
        )
        self.assertIsNotNone(notif.pk)
        self.assertEqual(notif.titulo, "Nueva notificación")
        self.assertEqual(notif.mensaje, "Tienes una nueva tarea pendiente")
        self.assertEqual(notif.usuario, self.user)

    def test_leida_default(self):
        notif = Notificacion.objects.create(usuario=self.user, titulo="Test", mensaje="Test")
        self.assertFalse(notif.leida)

    def test_str(self):
        notif = Notificacion.objects.create(usuario=self.user, titulo="Alerta", mensaje="Mensaje de prueba")
        self.assertEqual(str(notif), "Alerta - notifuser")

    def test_orden_fecha(self):
        Notificacion.objects.create(usuario=self.user, titulo="Primera", mensaje="Primera")
        Notificacion.objects.create(usuario=self.user, titulo="Segunda", mensaje="Segunda")
        notifs = list(Notificacion.objects.values_list("titulo", flat=True))
        self.assertEqual(notifs[0], "Segunda")
        self.assertEqual(notifs[1], "Primera")


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
class NotificacionViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="notifviewer", email="nv@test.com", password="testpass123")
        self.token = RefreshToken.for_user(self.user).access_token

        self.other_user = User.objects.create_user(username="other", email="other@test.com", password="testpass123")

    def test_list_requires_auth(self):
        response = self.client.get("/api/notificaciones/")
        self.assertEqual(response.status_code, 401)

    def test_list_own_notifications(self):
        Notificacion.objects.create(usuario=self.user, titulo="Mía", mensaje="Para mí")
        Notificacion.objects.create(usuario=self.other_user, titulo="Otra", mensaje="Otro usuario")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.token))
        response = self.client.get("/api/notificaciones/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["titulo"], "Mía")


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ],
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    NOTIFICACIONES_EMAIL_ENABLED=True,
)
class NotificacionEmailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="emailuser", email="email@test.com", password="testpass123")

    def test_crear_notificacion_envia_email(self):
        crear_notificacion(self.user, "Alerta", "Tienes un mensaje de prueba")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Alerta", mail.outbox[0].subject)
        self.assertIn(self.user.email, mail.outbox[0].to)

    @override_settings(NOTIFICACIONES_EMAIL_ENABLED=False)
    def test_crear_notificacion_sin_email_si_deshabilitado(self):
        crear_notificacion(self.user, "Titulo", "Mensaje")
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(Notificacion.objects.filter(usuario=self.user).exists())
