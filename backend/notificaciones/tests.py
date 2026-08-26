from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from .models import Notificacion


User = get_user_model()


@override_settings(PASSWORD_HASHERS=[
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
])
class NotificacionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='notifuser', email='notif@test.com', password='testpass123'
        )

    def test_crear(self):
        notif = Notificacion.objects.create(
            usuario=self.user,
            titulo='Nueva notificación',
            mensaje='Tienes una nueva tarea pendiente'
        )
        self.assertIsNotNone(notif.pk)
        self.assertEqual(notif.titulo, 'Nueva notificación')
        self.assertEqual(notif.mensaje, 'Tienes una nueva tarea pendiente')
        self.assertEqual(notif.usuario, self.user)

    def test_leida_default(self):
        notif = Notificacion.objects.create(
            usuario=self.user, titulo='Test', mensaje='Test'
        )
        self.assertFalse(notif.leida)

    def test_str(self):
        notif = Notificacion.objects.create(
            usuario=self.user,
            titulo='Alerta',
            mensaje='Mensaje de prueba'
        )
        self.assertEqual(str(notif), 'Alerta - notifuser')

    def test_orden_fecha(self):
        n1 = Notificacion.objects.create(
            usuario=self.user, titulo='Primera', mensaje='Primera'
        )
        n2 = Notificacion.objects.create(
            usuario=self.user, titulo='Segunda', mensaje='Segunda'
        )
        notifs = list(
            Notificacion.objects.values_list('titulo', flat=True)
        )
        self.assertEqual(notifs[0], 'Segunda')
        self.assertEqual(notifs[1], 'Primera')


@override_settings(PASSWORD_HASHERS=[
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
])
class NotificacionViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='notifviewer', email='nv@test.com', password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)

        self.other_user = User.objects.create_user(
            username='other', email='other@test.com', password='testpass123'
        )

    def test_list_requires_auth(self):
        response = self.client.get('/api/notificaciones/')
        self.assertEqual(response.status_code, 401)

    def test_list_own_notifications(self):
        Notificacion.objects.create(
            usuario=self.user, titulo='Mía', mensaje='Para mí'
        )
        Notificacion.objects.create(
            usuario=self.other_user, titulo='Otra', mensaje='Otro usuario'
        )
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get('/api/notificaciones/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['titulo'], 'Mía')
