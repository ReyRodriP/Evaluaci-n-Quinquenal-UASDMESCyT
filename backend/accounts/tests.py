from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.models import Group, Permission
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token


User = get_user_model()


class PasswordRecoveryTests(TestCase):
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_forgot_password_sends_email_for_registered_user(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            username='jane',
            email='jane@example.com',
            password='oldpassword123'
        )

        response = self.client.post(
            '/api/forgot_password',
            {'email': 'jane@example.com'},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Restablecimiento', mail.outbox[0].subject)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_forgot_password_is_generic_for_unknown_email(self):
        response = self.client.post(
            '/api/forgot_password',
            {'email': 'missing@example.com'},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_forgot_password_does_not_crash_when_email_delivery_fails(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            username='jane2',
            email='jane2@example.com',
            password='oldpassword123'
        )

        with patch('accounts.views.send_mail', side_effect=Exception('SMTP error')):
            response = self.client.post(
                '/api/forgot_password',
                {'email': 'jane2@example.com'},
                content_type='application/json'
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn('recuperar tu contraseña', response.json()['message'])

    def test_reset_password_accepts_valid_uid_and_token(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username='john',
            email='john@example.com',
            password='oldpassword123'
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = self.client.post(
            '/api/reset_password',
            {
                'uid': uid,
                'token': token,
                'new_password': 'newpassword123!'
            },
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpassword123!'))


class ObjectivesTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_group, _ = Group.objects.get_or_create(name='Administrador General')
        self.consulta_group, _ = Group.objects.get_or_create(name='Consulta')

        all_permissions = Permission.objects.all()
        self.admin_group.permissions.set(all_permissions)
        self.consulta_group.permissions.clear()

        self.admin_user = User.objects.create_user(
            username='admin', password='admin123', email='admin@test.com'
        )
        self.admin_user.groups.add(self.admin_group)

        self.consulta_user = User.objects.create_user(
            username='consulta', password='consulta123', email='consulta@test.com'
        )
        self.consulta_user.groups.add(self.consulta_group)

        self.admin_token = Token.objects.create(user=self.admin_user)
        self.consulta_token = Token.objects.create(user=self.consulta_user)

    # --- Objective 1: group_ids not allowed in register/profile ---
    def test_register_rejects_group_ids(self):
        response = self.client.post('/api/register', {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'pass123',
            'group_ids': [self.admin_group.id]
        })
        self.assertNotIn('group_ids', response.data.get('user', {}))
        user = User.objects.get(username='newuser')
        self.assertEqual(user.groups.count(), 0)

    def test_profile_rejects_group_ids(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.put('/api/profile', {
            'group_ids': [self.consulta_group.id]
        })
        user = User.objects.get(id=self.admin_user.id)
        self.assertEqual(user.groups.first().name, 'Administrador General')

    # --- Objective 2: permisos endpoint ---
    def test_permisos_endpoint_structure(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.get(f'/api/usuarios/{self.admin_user.id}/permisos/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.data)
        self.assertIn('username', response.data)
        self.assertIn('rol', response.data)
        self.assertIn('permisos', response.data)
        self.assertEqual(response.data['id'], self.admin_user.id)
        self.assertEqual(response.data['username'], 'admin')
        self.assertEqual(response.data['rol'], 'Administrador General')
        self.assertGreater(len(response.data['permisos']), 0)

    def test_permisos_endpoint_consulta(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.get(f'/api/usuarios/{self.consulta_user.id}/permisos/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['rol'], 'Consulta')
        self.assertEqual(len(response.data['permisos']), 0)

    # --- Objective 3: Seed permissions ---
    def test_admin_has_all_permissions(self):
        total = Permission.objects.count()
        self.assertEqual(self.admin_group.permissions.count(), total)

    def test_consulta_has_no_permissions(self):
        self.assertEqual(self.consulta_group.permissions.count(), 0)

    # --- Objective 4: CRUD protection ---
    def test_consulta_user_cannot_access_facultades(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.consulta_token.key)
        response = self.client.get('/api/facultades/')
        self.assertEqual(response.status_code, 403)

    def test_admin_user_can_access_facultades(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.get('/api/facultades/')
        self.assertEqual(response.status_code, 200)

    def test_consulta_user_cannot_access_periodos(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.consulta_token.key)
        response = self.client.get('/api/periodos/')
        self.assertEqual(response.status_code, 403)

    def test_admin_user_can_access_periodos(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.get('/api/periodos/')
        self.assertEqual(response.status_code, 200)

    def test_consulta_user_cannot_access_usuarios(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.consulta_token.key)
        response = self.client.get('/api/usuarios/')
        self.assertEqual(response.status_code, 403)

    def test_consulta_user_cannot_create_facultad(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.consulta_token.key)
        response = self.client.post('/api/facultades/', {'nombre': 'Test', 'descripcion': 'test'})
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_blocked(self):
        response = self.client.get('/api/facultades/')
        self.assertEqual(response.status_code, 401)
