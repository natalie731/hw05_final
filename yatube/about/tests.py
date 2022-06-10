'''
[х] - проверен ответ сервера
[х] - проверены шаблоны для URL
[х] - проверены шаблоны для views
'''
from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticPagesURLTests(TestCase):
    """Проверка ответа сервера и шаблонов страниц"""
    def setUp(self):
        self.guest_client = Client()

    def test_static_urls_exists_at_desired_location_for_all_users(self):
        """Сервер выдает ожидаемый ответ пользователю."""
        urls_location = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
            '/about/unexisting/': HTTPStatus.NOT_FOUND,
        }
        for url, location in urls_location.items():
            with self.subTest(msg=f'Aдрес {url} выдает '
                              'неверный ответ сервера.'):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, location)

    def test_static_urls_uses_correct_template(self):
        """URL-адреса использует соответствующий шаблон."""
        url_templates = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
            '/about/unexisting/': 'core/404.html',
        }
        for url, template in url_templates.items():
            with self.subTest(msg=f'Ошибка шаблона для адресa {url}.'):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_static_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        page_url_template = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for page_url, template in page_url_template.items():
            with self.subTest(msg=f'Ошибка шаблона для адресa {page_url}.'):
                response = self.guest_client.get(page_url)
                self.assertTemplateUsed(response, template)
