from http import HTTPStatus
from django.test import TestCase, Client
from django.urls import reverse
from ..models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="NoName")
        cls.user_no_author = User.objects.create(username="NoAuthor")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
        )
        cls.templates = [
            "/",
            f"/group/{cls.group.slug}/",
            f"/profile/{cls.user.username}/",
            f"/posts/{cls.post.pk}/",
        ]

        cls.templates_url_names = {
            "/": "posts/index.html",
            f"/group/{cls.group.slug}/": "posts/group_list.html",
            f"/profile/{cls.user.username}/": "posts/profile.html",
            f"/posts/{cls.post.pk}/": "posts/post_detail.html",
            f"/posts/{cls.post.pk}/edit/": "posts/create_post.html",
            "/create/": "posts/create_post.html",
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_no_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_no_author.force_login(self.user_no_author)



    def test_urls_uses_correct_template(self):
        for address in self.templates:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_post_id_edit_url_author(self):
        """Страница /posts/post_id/edit/ доступна автору."""
        response = self.authorized_client.get(f"/posts/{self.post.id}/edit/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_url_redirect(self):
        """Страница posts/post_id/edit/ перенаправляет на логин гостя."""
        response = self.guest_client.get(f'/posts/{self.post.pk}/edit/')
        auth_url = reverse('users:login')
        self.assertRedirects(
            response,
            f'{auth_url}?next=/posts/{self.post.pk}/edit/'
        )

    def test_edit_not_author_url_redirect(self):
        """Страница posts/post_id/edit/ перенаправляет на пост не автора."""
        response = self.authorized_client_no_author.get(
            f'/posts/{self.post.pk}/edit/'
        )
        self.assertRedirects(
            response,
            f'/posts/{self.post.pk}/'
        )

    def test_create_url_exists_at_desired_location_authorized(self):
        '''Станица /create/ доступна атовризированному юзеру'''
        response = self.authorized_client.get(
            ('/create/'),
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirect(self):
        """Страница /create/ перенаправляет на логин гостя."""
        response = self.guest_client.get('/create/')
        auth_url = reverse('users:login')
        self.assertRedirects(response, f"{auth_url}?next=/create/")

    def test_unexisting_page_url_exists_at_desired_location(self):
        """Страница /unexisting_page/ выдаёт ошибку"""
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in self.templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
