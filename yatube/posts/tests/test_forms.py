import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client, TestCase, override_settings

from posts.forms import PostForm
from posts.models import Group, Post, Comment
from posts.forms import CommentForm

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(text='Тестовый текст',
                                       author=cls.user)
        cls.comment = Comment.objects.create(text='Тестовый комментарий',
                                             author=cls.user,
                                             post=cls.post)
        cls.form = PostForm()
        cls.comm_form = CommentForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = Client()
        self.client.force_login(PostFormTests.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username': 'author'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(text=form_data['text'],
                                image='posts/small.gif').exists()
        )

    def test_edit_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Изменено',
        }
        response = self.client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': 1}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(pk=1).filter(text=form_data['text']).exists()
        )


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.post = Post.objects.create(text='Тестовый текст',
                                       author=cls.user)
        cls.comment = Comment.objects.create(text='Тестовый комментарий',
                                             author=cls.user,
                                             post=cls.post)
        cls.form = CommentForm()

    def setUp(self):
        self.client = Client()
        self.client.force_login(CommentFormTest.user)

    def test_create_comment(self):
        comm_count = Comment.objects.count()
        form_data = {
            'text': 'Комментарий',
        }
        response = self.client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': 1}))
        self.assertEqual(Post.objects.count(), comm_count)
        self.assertTrue(
            Comment.objects.filter(text=form_data['text']).exists()
        )
