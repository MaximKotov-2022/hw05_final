from http import HTTPStatus
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User, Comment


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="NameUser")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        '''Проверка создания поста'''
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.all()[0]
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)

    def test_edit_post(self):
        '''Проверка редактирования поста'''
        self.post = Post.objects.create(
            author=self.user,
            text='Текст',
        )
        post_data = {
            'text': 'Измененный тестовый текст',
            'group': self.group.pk,
        }
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=post_data,
            follow=True)
        post = Post.objects.all()[0]
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post.text, post_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)

    def test_comment(self):
        '''Проверка комментирования поста'''
        coment_count = Comment.objects.count()
        self.post = Post.objects.create(
            author=self.user,
            text='Текст',
        )
        form_data = {
            'author': self.user,
            'text': 'Текст комментария',
        }

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), coment_count + 1)
