from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_page_accessible_by_name(self):
        """URL, генерируемые при помощи имен 'about:', доступны"""
        names_list = {
            'about:author',
            'about:tech',
        }
        for url_name in names_list:
            with self.subTest(url_name=url_name):
                response = self.guest_client.get(reverse(url_name))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_page_uses_correct_template(self):
        """При запросе к именам about:author и tech
        применяется корректный шаблон"""
        names_list = {
            'about:author': 'about/author.html',
            'about:tech': 'about/tech.html',
        }
        for url_name, page_template in names_list.items():
            with self.subTest(url_name=url_name):
                response = self.guest_client.get(reverse(url_name))
                self.assertTemplateUsed(response, page_template)
