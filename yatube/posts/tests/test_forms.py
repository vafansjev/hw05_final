from ..forms import PostForm
from ..models import Group, Post

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

import shutil
import tempfile

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.user2 = User.objects.create_user(username='not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Описание тестовой группы'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.second_author = Client()
        self.second_author.force_login(self.user2)
        self.guest_client = Client()

    def test_create_post(self):
        """Валидная форма создает запись в Post из posts:create_post"""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Тестовый пост2',
            'group': self.group.id,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        reverse_page = reverse(
            'posts:profile', kwargs={'username': self.user})

        self.assertRedirects(response, reverse_page)
        self.assertEqual(Post.objects.count(), posts_count + 1)

        response2 = self.authorized_client.get(reverse_page)
        context = list(response2.context['page_obj'])
        self.assertEqual(context, list(Post.objects.all()))

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post из posts:edit_post"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост2',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.post.refresh_from_db()
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}
        ))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(self.post.text, form_data['text'])
        self.assertEqual(self.post.group.id, form_data['group'])

    def test_not_an_author_edit(self):
        """Проверка переадресации не автора при редактировании"""
        response = self.second_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))

    def test_guest_create_edit(self):
        """Проверка переадресации гостя на страницу авторизации
        при редактировании или создании поста"""
        reverse_list = {
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            f'/auth/login/?next=/posts/{str(self.post.id)}/edit/',
            reverse('posts:post_create'):
            '/auth/login/?next=/create/',
        }
        for url, redirect_url in reverse_list.items():
            with self.subTest(url=url):
                response = self.guest_client.post(
                    url,
                    follow=True
                )
                self.assertRedirects(response, redirect_url)

    def test_new_text_help_text(self):
        """Проверка help_text для нового поста"""
        text_help_text = PostCreateFormTests.form.fields['text'].help_text
        self.assertEqual(text_help_text, 'Текст нового поста')

    def test_group_help_text(self):
        """Проверка help_text для группы"""
        group_help_text = PostCreateFormTests.form.fields['group'].help_text
        self.assertEqual(
            group_help_text, 'Группа, к которой будет относиться пост')

    def test_auth_user_can_comment(self):
        """Проверка - Авторизованный пользователь может комментировать пост"""
        form_data = {
            'text': 'Тестовый комментарий',
            'author': self.user,
            'post': self.post,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        comment_object = response.context['comments'][0]
        self.assertEqual(comment_object.text, form_data['text'])

    def test_guest_cant_comment(self):
        """Проверка - Гость не может создавать пост"""
        form_data = {
            'text': 'Тестовый комментарий Гостя',
            'author': self.user,
            'post': self.post,
        }
        comments_count = self.post.comments.count()
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(comments_count, self.post.comments.count())
