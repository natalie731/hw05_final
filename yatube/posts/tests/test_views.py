'''
[X] - шаблоны соответствуют пространствам имен
[X] - для гостя: страницы /post/<post_id>/edit/ и
      /post/create/ делает редирект на login
[X] - для не автора: страница /post/<post_id>/edit/
      делает редирект на detail_post
[X] - шаблон index принимает правильный контент
      и правильно распределяет его паджинатором
[X] - шаблон group_list принимает правильный контент
      и правильно распределяет его паджинатором
[X] - в group_list только собственные посты.
[X] - шаблон profile принимает правильный контент
      и правильно распределяет его паджинатором
[X] - в profile только посты автора.
[X] - post_detail принимает корректный контекст
[X] - в формах create и post_edit ожидаемый контент

[X] - картинка попадает в контекст
[X] - картинка в форме корректна
[X] - для гостя: страницa /post/<post_id>/comment/
      делает редирект на login
[X] - в форму комментариев попадает правильный контекст
[X] - в комментарии попадает правильный контекст

[X] - после загрузки '/' в кеше хранятся данные до удаления

[Х} - follow_index - шаблон
[Х} - follow_index, profile_unfollow, profile_follow точный редирект
[ ] - пользователь подписывается
[ ] - пользователь отписывается
[ ] - новая запись появляется у подписчика
[ ] - новая запись НЕ появляется не подписчика
[ ] - самоподписок быть не может
'''
import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post, User
from ..views import COUNT_POST_ON_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
COUNT_POST_ON_TWO_PAGE = round(COUNT_POST_ON_PAGE / 2)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='posts/test.gif',
            content=test_gif,
            content_type='image/gif')
        cls.user = User.objects.create(username='auth')
        cls.alt_user = User.objects.create(username='alt_auth')
        cls.group = Group.objects.create(slug='test-slug')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=uploaded)
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.user,
            post=cls.post)

        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(
            PostPagesTests.user)
        cls.not_author_client = Client()
        cls.not_author_client.force_login(
            PostPagesTests.alt_user)

    def setUp(self) -> None:
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_page_uses_correct_template(self):
        """Namespace использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:group_list',
                    kwargs={'slug': PostPagesTests.group.slug}):
                        'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': PostPagesTests.user.username}):
                        'posts/profile.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': PostPagesTests.post.id}):
                        'posts/create_post.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': PostPagesTests.post.id}):
                        'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(msg=f'URL-адрес {reverse_name} '
                              f'использует шаблон {template}.'):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def func_redirect_control(self, client,
                              url_to_redirect_pages: dict) -> None:
        """Функция для контроля переадресаций.

        Arguments:
            url_to_redirect_pages -- словарь ключ: страница цель
                                             значение: страница редиректа
        """
        for url, redirect_page in url_to_redirect_pages.items():
            with self.subTest(url=url):
                response = client.get(url, follow=True)
                self.assertRedirects(response, redirect_page)

    def func_post_content_for_test(self, post_tested) -> dict:
        """Функция для компановки проверяемого и ожидаемого поста.

        Arguments:
            post_tested -- пост, полученный по запросую
        """
        post_expected: Post = self.post
        return {
            post_tested.id: post_expected.id,
            post_tested.author: post_expected.author,
            post_tested.group: post_expected.group,
            post_tested.text: post_expected.text,
            post_tested.pub_date: post_expected.pub_date,
            post_tested.image: post_expected.image,
        }

    def test_pages_uses_correct_redirect_for_guest_users(self):
        """
        Страницы, использующие редирект,
        для гостей верно выбирают адрес перенаправления.
        """
        user = PostPagesTests.user
        post = PostPagesTests.post
        url_to_redirect_pages = {
            reverse('posts:post_create'):
                '/auth/login/?next=/create/',
            reverse('posts:post_edit',
                    kwargs={'post_id': post.id}):
                        ('/auth/login/?next=/posts/'
                         f'{post.id}/edit/'),
            reverse('posts:add_comment',
                    kwargs={'post_id': post.id}):
                        ('/auth/login/?next=/posts/'
                         f'{post.id}/comment/'),
            reverse('posts:follow_index'):
                '/auth/login/?next=/follow/',
            reverse('posts:profile_follow',
                    kwargs={'username': user.username}):
                        ('/auth/login/?next=/profile/'
                         f'{user.username}/follow/'),
            reverse('posts:profile_unfollow',
                    kwargs={'username': user.username}):
                        ('/auth/login/?next=/profile/'
                         f'{user.username}/unfollow/'),
        }
        self.func_redirect_control(self.guest_client, url_to_redirect_pages)

    def test_pages_uses_correct_redirect_for_autorized_not_author_users(self):
        """
        Страницы, использующие редирект,
        для не автора поста верно выбирают адрес перенаправления.
        """
        post = PostPagesTests.post
        url_to_redirect_pages = {
            reverse('posts:post_edit', kwargs={'post_id': post.id}):
                f'/posts/{post.id}/',
        }
        self.func_redirect_control(self.not_author_client,
                                   url_to_redirect_pages)

    def func_assert_for_content_correct(self, test_data: dict) -> None:
        """Функция проверяет соответствие контента страницы ожидаемому.

        Arguments:
            test_data -- словарь ключ: тестируемые данные,
                                 значение: ожидаемые данные.
        """
        for tested, expected in test_data.items():
            with self.subTest(tested=tested):
                self.assertEqual(tested, expected)

    def form_test_func(self, form_fields: dict,
                       response_context: dict) -> None:
        """Функция проверяет соответствие полей формы ожидаемым типам.

        Arguments:
            form_fields -- словарь ключ: поле формы, значение: тип поля.
            response_context -- контекст формы.
        """
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response_context.fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_detail_page_show_correct_context(self):
        """В шаблон post_detail попадает nравильный контекст."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostPagesTests.post.id}))

        self.assertIn('post', response.context)
        test_data = self.func_post_content_for_test(
            response.context['post'])
        self.func_assert_for_content_correct(test_data)

        self.assertIn('form', response.context)
        form_fields = {'text': forms.fields.CharField}
        self.form_test_func(form_fields, response.context['form'])

        self.assertIn('comments', response.context)
        comment_tested: Comment = response.context['comments'][0]
        comment_expected: Comment = PostPagesTests.comment
        comment_meta = {
            comment_tested.author: comment_expected.author,
            comment_tested.text: comment_expected.text,
        }
        self.func_assert_for_content_correct(comment_meta)

        alt_post = Post.objects.create(
            text='Тест чужого комментария',
            author=PostPagesTests.user)
        alt_comment = Comment.objects.create(
            text='Другой комментарий',
            post=alt_post,
            author=self.user)
        self.assertNotIn(alt_comment, response.context['comments'])

    def test_index_page_index_show_correct_context(self):
        """В шаблон index попадает nравильный контекст."""
        response = self.authorized_client.get(
            reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        test_data = self.func_post_content_for_test(
            response.context['page_obj'][0])
        self.func_assert_for_content_correct(test_data)

    def test_group_list_page_show_correct_context(self):
        """В шаблон group_list попадает nравильный контекст."""
        slug = PostPagesTests.group.slug
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': slug}))

        self.assertIn('group', response.context)
        group_tested: Group = response.context['group']
        group_expected: Group = Group.objects.get(slug=slug)
        group_meta = {
            group_tested.slug: group_expected.slug,
            group_tested.title: group_expected.title,
            group_tested.description: group_expected.description,
        }
        self.func_assert_for_content_correct(group_meta)

        self.assertIn('page_obj', response.context)
        test_data = self.func_post_content_for_test(
            response.context['page_obj'][0])
        self.func_assert_for_content_correct(test_data)

        alt_group = Group.objects.create(
            slug='alt-slug')
        alt_post = Post.objects.create(
            text='Тест другой группы',
            author=PostPagesTests.user,
            group=alt_group)
        self.assertNotIn(alt_post, response.context['page_obj'])

    def test_profile_page_show_correct_context(self):
        """В шаблон profile попадает nравильный контекст."""
        username = PostPagesTests.user.username
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': username}))

        self.assertIn('author', response.context)
        author_tested: User = response.context['author']
        author_expected: User = User.objects.get(username=username)
        author_meta = {
            author_tested.username: author_expected.username,
            author_tested.first_name: author_expected.first_name,
            author_tested.last_name: author_expected.last_name,
        }
        self.func_assert_for_content_correct(author_meta)

        self.assertIn('page_obj', response.context)
        test_data = self.func_post_content_for_test(
            response.context['page_obj'][0])
        self.func_assert_for_content_correct(test_data)

        alt_post = Post.objects.create(
            text='Тест другого автора',
            author=PostPagesTests.alt_user)
        self.assertNotIn(alt_post, response.context['page_obj'])

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create и post_edit
        сформированы с правильным контекстом формы."""
        data_page = [reverse('posts:post_create'),
                     reverse('posts:post_edit',
                             kwargs={'post_id': PostPagesTests.post.id})]
        form_fields = {'text': forms.fields.CharField,
                       'group': forms.fields.ChoiceField,
                       'image': forms.fields.ImageField}
        for page in data_page:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertIn('form', response.context)
                self.form_test_func(form_fields, response.context['form'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.group = Group.objects.create(slug='test-slug')
        posts = [
            Post(
                author=cls.user,
                text='Тестовый пост',
                group=cls.group,
            ) for _ in range(COUNT_POST_ON_PAGE + COUNT_POST_ON_TWO_PAGE)
        ]
        Post.objects.bulk_create(posts)

    def test_pages_count_paginator_records(self):
        """Пагинатор выводит правильное количество записей на странице."""
        page_num_and_posts_count = {
            1: COUNT_POST_ON_PAGE,
            2: COUNT_POST_ON_TWO_PAGE,
        }
        page_for_test = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for page_num, post_count in page_num_and_posts_count.items():
            for reverse_page in page_for_test:
                with self.subTest(reverse_page=reverse_page):
                    response = self.client.get(reverse_page,
                                               {'page': page_num})
                    self.assertEqual(len(
                        response.context['page_obj']), post_count)


class PostCacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.post = Post.objects.create(author=cls.user)
        cls.guest_client = Client()

    def setUp(self) -> None:
        cache.clear()

    def test_cache_ingex_page_view(self) -> None:
        """Контент index page попадает в кеш."""
        self.guest_client.get(
            reverse('posts:index'))
        self.post.delete()
        self.assertEqual(len(cache.get('index_page')), 1)
        cache.clear()

        self.guest_client.get(
            reverse('posts:index'))
        self.assertEqual(len(cache.get('index_page')), 0)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.alt_user = User.objects.create(username='alt_auth')
        cls.author = User.objects.create(username='author')
        cls.post = Post.objects.create(author=cls.author,
                                       text='Тестовый пост')
        Follow.objects.create(user=cls.user, author=cls.author)

        cls.authorized_client = Client()
        cls.authorized_client.force_login(
            FollowTests.user)
        cls.alt_authorized_client = Client()
        cls.alt_authorized_client.force_login(
            FollowTests.alt_user)

    def test_follow_page__show_correct_context(self):
        """В шаблон follow попадает nравильный контекст."""
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertIn('page_obj', response.context)
        post_tested = response.context['page_obj'][0]
        post_expected: Post = self.post
        test_data = {
            post_tested.id: post_expected.id,
            post_tested.author: post_expected.author,
            post_tested.group: post_expected.group,
            post_tested.text: post_expected.text,
            post_tested.pub_date: post_expected.pub_date,
            post_tested.image: post_expected.image,
        }
        for tested, expected in test_data.items():
            with self.subTest(tested=tested):
                self.assertEqual(tested, expected)

        response = self.alt_authorized_client.get(
            reverse('posts:follow_index'))
        self.assertIn('page_obj', response.context)
        post_tested = response.context['page_obj']
        self.assertNotEqual(post_tested, self.post)
