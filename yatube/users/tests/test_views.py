from django.test import Client, TestCase
from django.urls import reverse
from django import forms


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_signup_page_uses_correct_template(self):
        """При запросе к users:signup
        применяется корректный шаблон"""
        response = self.guest_client.get(reverse('users:signup'))
        self.assertTemplateUsed(response, 'users/signup.html')

    def test_signup_context(self):
        """Проверка контекста формы создания пользователя"""
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.CharField,
            'password1': forms.fields.CharField,
            'password2': forms.fields.CharField,
        }
        response = self.guest_client.get(reverse('users:signup'))
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
