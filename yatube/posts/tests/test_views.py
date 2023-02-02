from django import forms
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from yatube.settings import NUM_OF_POSTS

from ..models import Group, Post, User, Follow


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="StasBasov")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": self.post.author}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": self.post.pk}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": self.post.pk}
            ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
            ('NoSiteUrl'): 'core/404.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        records = list(Post.objects.all()[:NUM_OF_POSTS])
        self.assertEqual(list(response.context['page_obj']), records)
        url_page = self.client.get(reverse('posts:index'))
        self.assertIn('<img', url_page.content.decode())

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        records = list(
            Post.objects.filter(group_id=self.group.id)[:NUM_OF_POSTS]
        )
        self.assertEqual(list(response.context['page_obj']), records)
        self.assertEqual(response.context['group'], self.post.group)
        self.assertIn('page_obj', response.context)
        self.assertTrue(len(response.context['page_obj']))
        post_image = response.context['page_obj'][0]
        self.assertEqual(post_image.image, self.post.image)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        records = list(
            Post.objects.filter(author_id=self.user.id)[:NUM_OF_POSTS]
        )
        self.assertEqual(list(response.context['page_obj']), records)
        self.assertEqual(response.context['author'], self.post.author)
        url_page = self.client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        self.assertIn('<img', url_page.content.decode())

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        pointer_response = response.context['post']
        self.assertEqual((pointer_response.text), str(self.post.text))
        self.assertEqual((pointer_response.author), (self.post.author))
        self.assertEqual((pointer_response.group), (self.post.group))
        url_page = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertIn('<img', url_page.content.decode())

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_edit_show_correct_context(self):
        """Шаблон post_create_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context['is_edit'])
        self.assertEqual(response.context['post_id'], self.post.pk)

    def test_create_post_site_group_correct(self):
        """При создании поста он не появляется стр другой группы"""
        form_fields = {
            reverse("posts:index"): Post.objects.get(group=self.post.group),
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse(
                "posts:profile", kwargs={"username": self.post.author}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertIn(expected, form_field)

    def test_cache_index(self):
        '''Проверка кэширования.'''
        response_1 = self.client.get(reverse('posts:index'))
        self.assertContains(response_1, self.post)

        Post.objects.filter(pk=1).delete()

        response_2 = self.client.get(reverse('posts:index'))
        self.assertContains(response_2, self.post)

        cache.clear()

        response_3 = self.client.get(reverse('posts:index'))
        self.assertNotContains(response_3, self.post)

    def test_follow_author(self):
        '''Проверка подписки на автора на которого не подписан юзер'''
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)

        Follow.objects.get_or_create(
            user=self.user,
            author=self.post.author
        )
        response_create = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response_create.context['page_obj']), 1)

    def test_unfollow_author(self):
        '''Проверка отписки от автора на которого подписан юзер'''
        response = self.authorized_client.get(reverse('posts:follow_index'))
        Follow.objects.get_or_create(
            user=self.user,
            author=self.post.author
        )
        Follow.objects.get(
            user=self.user,
            author=self.post.author
        ).delete()
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_show_follow_of_follow(self):
        '''Проверка появления поста у юзера с подписками'''
        Follow.objects.get_or_create(
            user=self.user,
            author=self.post.author
        )
        Post.objects.create(
            author=self.user,
            text='Тестовый пост для подписчика',
            group=self.group,
        )
        response_page_follow = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(str(self.post), response_page_follow.content.decode())

    def test_not_show_unfollow(self):
        '''Пост не появляется на странице подписок у не-подписчика'''
        user_no_follow = User.objects.create(username='NoFollowUser')
        self.authorized_client.force_login(user_no_follow)
        responce_no_follow = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(responce_no_follow.context['page_obj']), 0)


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.PAGE_NUM = 13
        cls.user = User.objects.create(username="Name")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug2",
            description="Тестовое описание2",
        )

        Post.objects.bulk_create([
            Post(
                text=f"Тестовый текст{i}",
                author=cls.user, group=cls.group)
            for i in range(cls.PAGE_NUM)
        ])

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        """Шаблон сформирован с правильным паджинатором_1."""
        NUM_POSTS = 10
        templates_pages = [
            reverse("posts:index"),
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ),
            reverse(
                "posts:profile", kwargs={"username": self.user.username}
            ),
        ]
        for pages in templates_pages:
            with self.subTest(reverse_name=pages):
                response = self.client.get(pages)
                self.assertEqual(
                    len(response.context["page_obj"]), NUM_POSTS)

    def test_second_page_contains_three_records(self):
        """Шаблон сформирован с правильным паджинатором_2."""
        NUM_POSTS = 3
        templates_pages_names = {
            "posts/index.html": reverse("posts:index") + "?page=2",
            "posts/group_list.html": reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            )
            + "?page=2",
            "posts/profile.html": reverse(
                "posts:profile", kwargs={"username": self.user.username}
            )
            + "?page=2",
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(
                    len(response.context["page_obj"]), NUM_POSTS)
