import shutil
import tempfile

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, Follow
from posts.views import OUT_LIMIT
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')

    def setUp(self):
        self.client = Client()
        self.nofl_client = Client()
        self.client.force_login(FollowTest.user)
        self.nofl_client.force_login(FollowTest.author)

    def test_follow_view(self):
        fltr_obj = (Follow.objects.filter(user=FollowTest.user).
                    filter(author=FollowTest.author))
        self.assertFalse(fltr_obj.exists())
        self.client.get(reverse('posts:profile_follow',
                                kwargs={'username': 'author'}))
        self.assertTrue(fltr_obj.exists())

    def test_unfollow_view(self):
        Follow.objects.create(user=FollowTest.user, author=FollowTest.author)
        (Follow.objects.filter(user=FollowTest.user).
         filter(author=FollowTest.author)).delete()
        self.assertFalse(Follow.objects.filter(user=FollowTest.user).
                         filter(author=FollowTest.author).exists())

    def test_create_post_for_followers(self):
        post = Post.objects.create(author=FollowTest.author, text='Text')
        Follow.objects.create(user=FollowTest.user, author=FollowTest.author)
        response = self.client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context['page_obj'][0], post)

    def test_create_post_for_nofollowers(self):
        post = Post.objects.create(author=FollowTest.author, text='Text')
        response = self.nofl_client.get(reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'])


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')

    def setUp(self):
        user = CacheTest.user
        self.client = Client()
        self.client.force_login(user)
        self.post = Post.objects.create(author=CacheTest.user,
                                        text='Test Post')

    def test_cache_view_nosave(self):
        response = self.client.get(reverse('posts:index'))
        self.assertIn(self.post, response.context['page_obj'])
        Post.objects.filter(pk=1).delete()
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_cache_view_save(self):
        response = self.client.get(reverse('posts:index'))
        self.assertIn(self.post, response.context['page_obj'])
        Post.objects.filter(pk=1).delete()
        self.assertIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = Post.objects.bulk_create([Post(text="Check",
                                                   group=cls.group,
                                                   author=cls.user)] * 13)

    def setUp(self):
        user = PaginatorViewsTest.user
        self.client = Client()
        self.client.force_login(user)

    def test_paginator_pages(self):
        RMD = 3
        urls_with_count = {
            reverse('posts:index'): OUT_LIMIT,
            reverse('posts:index') + '?page=2': RMD,
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}): OUT_LIMIT,
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}) + '?page=2': RMD,
            reverse('posts:profile',
                    kwargs={'username': 'author'}): OUT_LIMIT,
            reverse('posts:profile',
                    kwargs={'username': 'author'}) + '?page=2': RMD,
        }
        for url, post_count in urls_with_count.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(len(response.context['page_obj']), post_count)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
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
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        user = PostPagesTests.user
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': 1}): 'posts'
            '/create_post.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}): 'posts'
            '/group_list.html',
            reverse('posts:post_detail', kwargs={'post_id': 1}): 'posts'
            '/post_detail.html',
            reverse('posts:profile', kwargs={'username': 'author'}): 'posts'
            '/profile.html',
        }
        for url, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        test_title = response.context['title']
        test_obj = response.context['page_obj'][0]
        self.assertEqual(test_title, 'Последние обновления на сайте')
        self.assertEqual(test_obj.text, PostPagesTests.post.text)
        self.assertEqual(test_obj.author, PostPagesTests.user)
        self.assertEqual(test_obj.image, PostPagesTests.post.image)

    def test_group_list_correct_context(self):
        response = self.authorized_client.get(reverse('posts:group_list',
                                              kwargs={'slug': 'test-slug'}))

        test_title = response.context['title']
        test_obj = response.context['page_obj'][0]
        self.assertEqual(test_title, f'Записи сообщества '
                         f'{PostPagesTests.group.title}')
        self.assertEqual(test_obj.text, PostPagesTests.post.text)
        self.assertEqual(test_obj.author, PostPagesTests.user)
        self.assertEqual(test_obj.image, PostPagesTests.post.image)

    def test_profile_correct_context(self):
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': 'author'}))
        test_author = response.context['author']
        test_obj = response.context['page_obj'][0]
        test_count = response.context['count']
        self.assertEqual(test_author, PostPagesTests.user)
        self.assertEqual(test_obj.text, PostPagesTests.post.text)
        self.assertEqual(test_obj.author, PostPagesTests.user)
        self.assertEqual(test_obj.image, PostPagesTests.post.image)
        self.assertEqual(test_count, 1)

    def test_post_detail_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_detail',
                                              kwargs={'post_id': 1}))
        test_post = response.context['post']
        test_count = response.context['count']
        self.assertEqual(test_post, PostPagesTests.post)
        self.assertEqual(test_count, 1)

    def test_create_post_correct_context(self):
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

    def test_edit_post_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_edit',
                                              kwargs={'post_id': 1}))
        test_id = response.context['post_id']
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(test_id, 1)
