from http import HTTPStatus

from django.test import Client, TestCase
from ..forms import User


class UsersURLTests(TestCase):
    """Проверка ответа сервера и шаблонов страниц"""
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username='auth')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_users_urls_desired_server_answer_for_guest_user(self):
        """Сервер выдает ожидаемый ответ любому пользователю."""
        urls_answer = {
            '/auth/reset/done/': HTTPStatus.OK,
            '/auth/reset/<uidb64>/<token>/': HTTPStatus.OK,
            '/auth/password_reset/done/': HTTPStatus.OK,
            '/auth/password_reset/': HTTPStatus.OK,
            '/auth/login/': HTTPStatus.OK,
            '/auth/signup/': HTTPStatus.OK,
            '/auth/logout/': HTTPStatus.OK,
            '/auth/password_change/done/': HTTPStatus.FOUND,
            '/auth/password_change/': HTTPStatus.FOUND,
            '/auth/unexisting/': HTTPStatus.NOT_FOUND,
        }
        for url, answer in urls_answer.items():
            with self.subTest(msg=f'Aдрес {url} выдает '
                              'неверный ответ сервера.'):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, answer)

    def test_users_urls_desired_server_answer_for_authorized_user(self):
        """Сервер выдает ожидаемый ответ авторизированному пользователю."""
        urls_answer = {
            '/auth/password_change/done/': HTTPStatus.OK,
            '/auth/password_change/': HTTPStatus.OK,
        }
        for url, answer in urls_answer.items():
            with self.subTest(msg=f'Aдрес {url} выдает '
                              'неверный ответ сервера.'):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, answer)

    def test_users_urls_uses_correct_template(self):
        """URL-адреса использует соответствующий шаблон."""
        url_templates = {
            '/auth/signup/': 'users/signup.html',
            '/auth/unexisting/': 'core/404.html',
        }
        for url, template in url_templates.items():
            with self.subTest(msg=f'Ошибка шаблона для адресa {url}.'):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
