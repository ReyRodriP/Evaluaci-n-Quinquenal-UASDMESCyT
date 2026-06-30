from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


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
