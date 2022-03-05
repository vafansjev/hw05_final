from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        post = PostModelTest.post
        expected_group_name = group.title
        expected_post_name = post.text[:15]
        self.assertEqual(expected_group_name, str(group))
        self.assertEqual(expected_post_name, str(post))

    def test_post_verbose_text(self):
        """Проверка наличия verbose_name у полей модели Post"""
        post = PostModelTest.post
        verbose_fields = {
            'text': 'Текст поста',
            'pub_date': 'Дата создания',
            'update_date': 'Дата редактирования',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in verbose_fields.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value)

    def test_post_help_text(self):
        """Проверка наличия help_text у полей модели Post"""
        post = PostModelTest.post
        help_fields = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in help_fields.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value)
