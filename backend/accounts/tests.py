from django.test import TestCase
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

User = get_user_model()


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
