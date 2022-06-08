'''
[X] - Форма сохраняет пост
[X] - Форма правит пост

[X] - Форма CommentForm сохраняет новый комментарий
'''
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
FILE_NAME = 'test.gif'


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(slug='test-slug')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост')

        cls.authorized_client = Client()
        cls.authorized_client.force_login(PostCreateFormTests.user)

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def content_create_for_post(self, post_text: str) -> dict:
        """Создание картинки и сбор данных в словарь
        с полями Post.

        Arguments:
            post_text -- текст поста

        Returns:
            Словарь с заполненными полями формы
        """
        test_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name=FILE_NAME,
            content=test_gif,
            content_type='image/gif')
        return {'text': post_text,
                'group': PostCreateFormTests.group.id,
                'author': PostCreateFormTests.user,
                'image': uploaded}

    def form_post_active_data_and_valid_redirect(self, form_data: dict,
                                                 form_active,
                                                 valid_redirect) -> None:
        """Проверка формы постов на редирект и наличие поста в базе.

        Arguments:
            form_data -- данные для записи в форму
            form_active -- запрос формы
            valid_redirect -- запрос после валидации и записи
        """
        response = self.authorized_client.post(
            form_active,
            data=form_data,
            follow=True)
        self.assertRedirects(response, valid_redirect)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=PostCreateFormTests.user,
                group=PostCreateFormTests.group,
                image=f'posts/{FILE_NAME}').exists())

    def test_form_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        post_count = Post.objects.count()
        form_data = self.content_create_for_post('Отредактированный пост')
        self.form_post_active_data_and_valid_redirect(
            form_data,
            reverse('posts:post_edit',
                    kwargs={'post_id': PostCreateFormTests.post.id}),
            reverse('posts:post_detail',
                    kwargs={'post_id': PostCreateFormTests.post.id}))
        self.assertEqual(Post.objects.count(), post_count)

    def test_form_save_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        form_data = self.content_create_for_post('Новый пост')
        self.form_post_active_data_and_valid_redirect(
            form_data,
            reverse('posts:post_create'),
            reverse('posts:profile',
                    kwargs={'username': PostCreateFormTests.user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_form_save_comment(self):
        """Валидная форма создает комментарий в Comment."""
        post = PostCreateFormTests.post
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Новый комментарий',
            'post': post,
            'author': PostCreateFormTests.user,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': post.id}))
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                author=PostCreateFormTests.user,
                post=PostCreateFormTests.post).exists())
        self.assertEqual(Comment.objects.count(), comment_count + 1)


class FollowDBTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.alt_user = User.objects.create_user(username='alt_auth')
        cls.author = User.objects.create(username='author')
        cls.post = Post.objects.create(author=cls.author)
        Follow.objects.create(user=cls.alt_user, author=cls.author)

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.alt_authorized_client = Client()
        cls.alt_authorized_client.force_login(cls.alt_user)
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

    def test_save_follow(self):
        """Подписка сохраняется в базу."""
        follow_count = Follow.objects.count()
        response = self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author}))
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.author}))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.author).exists())
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_no_save_double_follow(self):
        """Дубль подписка не сохраняется в базу."""
        follow_count = Follow.objects.count()
        self.alt_authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author}))
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_delete_follow(self):
        """Подписка удаляется из базы."""
        follow_count = Follow.objects.count()
        response = self.alt_authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author}))
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.author}))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author).exists())
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_double_delete_follow_redirect(self):
        """Удаление пустой подписки вызывает редирект."""
        response = self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author}))
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.author}))

    def test_delete_follow(self):
        """Автор не может подписаться сам на себя."""
        follow_count = Follow.objects.count()
        response = self.author_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author}))
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.author}))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author).exists())
        self.assertEqual(Follow.objects.count(), follow_count)
