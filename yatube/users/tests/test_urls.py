from django.test import TestCase, Client
from http import HTTPStatus


class UsersPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_signup_accessed(self):
        """Проверка доступности адреса /singup/"""
        response = self.guest_client.get('/auth/signup/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_signup_template(self):
        """Проверка соответствия /signup/ шаблону"""
        response = self.guest_client.get('/auth/signup/')
        self.assertTemplateUsed(response, 'users/signup.html')
