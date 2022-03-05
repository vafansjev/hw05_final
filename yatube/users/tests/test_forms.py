from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_create_new_user(self):
        """Валидная форма создает нового пользователя"""
        users_count = User.objects.count()
        form_data = {
            'username': 'TestUser',
            'password1': 'Pa123ssword',
            'password2': 'Pa123ssword',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), users_count + 1)
