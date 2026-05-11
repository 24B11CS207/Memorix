from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='learner', password='StrongPass123')

    def test_user_can_login_with_django_session(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'learner',
            'password': 'StrongPass123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse('dashboard:home'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response['Location'])

    def test_legacy_dashboard_path_uses_django_auth_flow(self):
        response = self.client.get('/dashboard.html')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('dashboard:home'))
