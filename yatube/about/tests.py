from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_static_url_exists_at_desired_location(self):
        """Проверка доступности статичных адресов."""
        urls = ['/about/author/', '/about/tech/']
        for url in urls:
            with self.subTest(msg=f'Проверка доступности адресa {url}.'):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_static_url_uses_correct_template(self):
        """Проверка шаблонов для статичных адресов."""
        data_templates = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, template in data_templates.items():
            with self.subTest(msg=f'Проверка шаблона для адресa {url}.'):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_author_page_accessible_by_name(self):
        """URL, генерируемый при помощи имени about:<>, доступен."""
        page_url = [reverse('about:author'), reverse('about:tech')]
        for url in page_url:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_tech_page_uses_correct_template(self):
        """При запросе к about:<>
        применяется корректный шаблон."""
        page_url_template = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for page_url, template in page_url_template.items():
            with self.subTest(page_url=page_url):
                response = self.guest_client.get(page_url)
                self.assertTemplateUsed(response, template)
