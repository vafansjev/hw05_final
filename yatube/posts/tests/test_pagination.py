from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from ..models import Group, Post

User = get_user_model()

PAGINATOR_PAGES_COUNT = 10


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Описание тестовой группы'
        )
        for i in range(1, 15):
            Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group,
            )

        cls.post = Post.objects.first()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_page_paginator(self):
        """Проверка паджинатора на странице index"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context['page_obj']), PAGINATOR_PAGES_COUNT)

    def test_group_page_paginator(self):
        """Проверка паджинатора на странице group_list"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(
            len(response.context['page_obj']), PAGINATOR_PAGES_COUNT)

    def test_profile_page_paginator(self):
        """Проверка паджинатора на странице profile"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(
            len(response.context['page_obj']), PAGINATOR_PAGES_COUNT)
