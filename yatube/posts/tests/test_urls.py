from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

from http import HTTPStatus

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def setUp(self):
        user = PostURLTests.user
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(user)

    def test_haveno_page(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_guest(self):
        url_names = [
            '/',
            '/group/test-slug/',
            '/profile/author/',
            '/posts/1/',
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_auth(self):
        url_names = [
            '/create/',
            '/posts/1/edit/',
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect_anonymus(self):
        url_names = [
            '/create/',
            '/posts/1/edit/',
        ]
        for address in url_names:
            with self.subTest(adress=address):
                response = self.guest_client.get(address, follow=True)
                log_url = '/auth/login/?next='
                next_url = log_url + address
                self.assertRedirects(response, next_url)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/posts/1/': 'posts/post_detail.html',
            '/profile/author/': 'posts/profile.html',
            '/unexisting_page/': 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
