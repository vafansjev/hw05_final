from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_public_pages_available(self):
        """Проверка общедоступных страницы без авторизации"""
        page_list = {
            '/',
            '/group/' + self.group.slug + '/',
            '/profile/' + self.user.username + '/',
            '/posts/' + str(self.post.id) + '/',
        }
        for page in page_list:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisted_page(self):
        """Проверка получения 404 по несуществующей страницы"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_create_page_authorized(self):
        """Проверка create/ и post/edit для авторизованного"""
        page_list = {
            '/create/',
            '/posts/' + str(self.post.id) + '/edit/',
        }
        for page in page_list:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_page_redirect(self):
        """Проверка create/ и post/edit для НЕ авторизованного"""
        page_list = {
            '/create/': '/auth/login/?next=/create/',
            '/posts/' + str(self.post.id) + '/edit/':
            '/auth/login/?next=/posts/' + str(self.post.id) + '/edit/',
        }
        for url, redirect_url in page_list.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect_url)

    def test_urls_templates(self):
        """Проверка соответствия шаблонам urls"""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/' + self.group.slug + '/': 'posts/group_list.html',
            '/profile/' + self.user.username + '/': 'posts/profile.html',
            '/posts/' + str(self.post.id) + '/': 'posts/post_detail.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
