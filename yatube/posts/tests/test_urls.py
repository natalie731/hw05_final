'''
[X] - общедоступный /, /group/slug/, /post/id/, profile/username == 200
[X] - гость /сreate, /post/id/edit == 302
[X] - авторизация не автора поста /post/id/edit == 302
[Х] - /unexisting, /group/unexisting, /post/unexisting,
      /post/unexisting/edit, /profile/unexisting == 404 шаблон 404.html
[X] - Шаблоны 6-ти страниц

[X] - гость /post/id/comment == 302
[Х] - /posts/test/comment/ == 404 и шаблон 404.html

[X] - гость /follow/, /profile/username/follow,
      /profile/username/unfollow == 302
[X] - /follow/ шаблон
[X] - /profile/unexisting/follow/,
      /profile/unexisting/unfollow/ == 404 шаблон 404.html
'''

from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.post = Post.objects.create(author=cls.user)
        cls.group = Group.objects.create(slug='test-slug')

        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_not_author_client = Client()
        cls.user_not_author = User.objects.create(username='NotAuthor')
        cls.authorized_not_author_client.force_login(cls.user_not_author)

    def setUp(self) -> None:
        cache.clear()

    def test_url_ok_for_all_users(self):
        """URL доступен любому пользователю."""
        data_urls = [
            f'/group/{PostURLTests.group.slug}/',
            f'/profile/{PostURLTests.user.username}/',
            f'/posts/{PostURLTests.post.id}/',
            '/',
        ]
        for url in data_urls:
            with self.subTest(msg=f'Страница {url} доступна '
                              'любому пользователю.'):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_ok_for_authorized(self):
        """URL доступен авторизированному пользователю."""
        data_urls = [
            f'/posts/{PostURLTests.post.id}/edit/',
            '/create/',
        ]
        for url in data_urls:
            with self.subTest(msg=f'Страница {url} доступна '
                              'авторизированному пользователю.'):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_redirect_for_anonymous(self):
        """URL перенаправляет анонимного пользователя."""
        data_urls = [
            f'/posts/{PostURLTests.post.id}/edit/',
            '/create/',
            f'/posts/{PostURLTests.post.id}/comment/',
            '/follow/',
            f'/profile/{PostURLTests.user.username}/follow/',
            f'/profile/{PostURLTests.user.username}/unfollow/'
        ]
        for url in data_urls:
            with self.subTest(msg=f'Страница {url} перенаправляет '
                              'анонимного пользователя.'):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_posts_edit_url_redirect_authorized_not_author(self):
        """URL перенаправляет авторизированного не автора поста."""
        response = self.authorized_not_author_client.get(
            f'/posts/{PostURLTests.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_wrong_url_returns_not_found(self):
        """Несуществующий URL возвращает 404 и берет нужный шаблон"""
        wrong_url = [
            '/group/unexisting/',
            '/profile/unexisting/',
            '/posts/unexisting/edit',
            '/posts/unexisting/',
            '/unexisting_page/',
            '/posts/unexisting/comment/',
            '/profile/unexisting/follow/',
            '/profile/unexisting/unfollow/',
        ]
        for url in wrong_url:
            with self.subTest(msg=f'Несуществующая страница {url} '
                              'возвращает 404 и шаблон 404.html'):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
                self.assertTemplateUsed(response, 'core/404.html')

    def test_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        data_templates = {
            '/follow/': 'posts/follow.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/create_post.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/': 'posts/index.html',
        }
        for url, template in data_templates.items():
            with self.subTest(msg=f'Проверка шаблона для адресa {url}.'):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
