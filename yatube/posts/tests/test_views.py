from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Group, Post, Follow

import shutil
import tempfile

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Описание тестовой группы'
        )

        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='slug-2',
            description='Описание тестовой группы2'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """Проверка корректности namespase:name View Posts"""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template,)

    def test_post_pages_correct_context(self):
        """Проверка шаблонов index, group_list, profile на контекст"""
        response_list = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        }
        for reverse_name in response_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                context = list(response.context['page_obj'])
                self.assertEqual(context, list(Post.objects.all()[:10]))

    def test_post_detail_correct_context(self):
        """Шаблон формы post_detail сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        context = response.context['post']
        self.assertEqual(context, self.post)

    def test_post_edit_create_show_correct_context(self):
        """Шаблоны форм create и edit сформированы с правильным контекстом"""
        reverse_list = {
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        }
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for reverse_value in reverse_list:
            response = self.authorized_client.get(reverse_value)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_create_correct(self):
        """Проверка при создании поста:
        -Есть на главной странице;
        -Есть на странице выбранной группы;
        -Есть в профайле пользователя"""
        reverse_names = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        }
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                context = list(response.context['page_obj'])
                self.assertIn(self.post, context)

    def test_post_in_right_group(self):
        """Проверка, что пост из первой группы не попал во вторую"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group2.slug})
        )
        context = list(response.context['page_obj'])
        self.assertNotIn(self.post, context)

    def test_post_pages_correct_image_context(self):
        """Проверка шаблонов index, group_list, profile
        на наличие изображения в контексте"""
        response_list = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        }
        for reverse_name in response_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                test_image = response.context['page_obj'].object_list[0].image
                self.assertEqual(test_image, self.post.image,
                                 f'Нет изображения в посте {reverse_name}')

    def test_post_detail_correct_image_context(self):
        """Проверка наличия изображения в контексте post_detail"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        test_image = response.context['post'].image
        self.assertEqual(test_image, self.post.image)

    def test_index_cache(self):
        """Проверка кэширования главной страницы"""
        default_response = self.authorized_client.get(
            reverse('posts:index')
        )
        new_post = Post.objects.create(text='cache test', author=self.user)
        create_response = self.authorized_client.get(reverse('posts:index'))

        new_post.delete()

        delete_response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(create_response.content, delete_response.content)

        cache.clear()

        clean_response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(default_response.content, clean_response.content)

    def test_authorized_can_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей только 1 раз
        и пользователь может удалять их из подписок."""
        new_user = User.objects.create_user(username='new_follower')
        follower = Client()
        follower.force_login(new_user)
        follow_reverse = reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}
        )
        unfollow_reverse = reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user.username}
        )

        follower.get(follow_reverse)
        follow_count = Follow.objects.count()
        self.assertEqual(follow_count, 1)

        follower.get(follow_reverse)
        follow_count = Follow.objects.count()
        self.assertEqual(follow_count, 1)

        follower.get(unfollow_reverse)
        follow_count = Follow.objects.count()
        self.assertEqual(follow_count, 0)

    def test_new_post_followers(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""

        new_user1 = User.objects.create_user(username='new_follower')
        follower = Client()
        follower.force_login(new_user1)

        new_user2 = User.objects.create_user(username='new_Not_follower')
        not_follower = Client()
        not_follower.force_login(new_user2)

        Post.objects.create(
            author=self.user,
            text='Новый пост',
        )

        follow_reverse = reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}
        )

        index_reverse = reverse('posts:follow_index')

        follower.get(follow_reverse)
        posts_count = Post.objects.filter(author_id=self.user.id).count()
        response = follower.get(index_reverse)
        context = response.context['page_obj'].object_list
        follow_count = len(list(context))
        self.assertEqual(follow_count, posts_count)

        response = not_follower.get(index_reverse)
        context = response.context['page_obj'].object_list
        follow_count = len(list(context))
        self.assertNotEqual(follow_count, posts_count)
