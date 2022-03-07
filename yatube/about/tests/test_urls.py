from django.test import TestCase, Client
from http import HTTPStatus


class AboutPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адреса /about/author/"""
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_tech_url_exists_at_desired_location(self):
        """Проверка доступности адреса /about/tech/."""
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблона для адреса /about/author/ и /tech/."""
        page_list = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for test_page, page_template in page_list.items():
            with self.subTest(test_page=test_page):
                response = self.guest_client.get(test_page)
                self.assertTemplateUsed(response, page_template)
