'''
[X] - Проверена длинная __str__ для Post
[X] - Проверена длинная __str__ для Group
[Х] - verbose_name в Post соответствует 'Текст поста'
      и в Group 'Группа'
[Х] - help_text в Post соответствует 'Текст нового поста'
      и в Group 'Группа, к которой будет относиться пост'

[X] - Проверена длинная __str__ для Comment
'''
from core.models import LETTERS_IN_STR
from django.test import TestCase

from ..models import Comment, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа для магии',
            slug='test-slug_L')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для магии')
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='Тестовый комментарий')

    def test_models_have_correct__str__(self) -> None:
        """Проверяем, что у моделей корректно работает __str__."""
        data_objects = {
            PostModelTest.group:
                PostModelTest.group.title,
            PostModelTest.post:
                PostModelTest.post.text[:LETTERS_IN_STR],
            PostModelTest.comment:
                PostModelTest.comment.text[:LETTERS_IN_STR]
        }
        for testable, value in data_objects.items():
            with self.subTest(testable=testable):
                self.assertEqual(str(testable), value)

    def test_post_have_correct_verbose_names(self) -> None:
        """verbose_name в полях Post совпадает с ожидаемым."""
        data = {
            'group': 'Группа',
            'text': 'Текст поста',
            'image': 'Картинка',
        }
        for field, expected in data.items():
            with self.subTest(field=field):
                testable = (
                    PostModelTest.post._meta.get_field(field).verbose_name)
                self.assertEqual(testable, expected)

    def test_post_have_correct_help_textes(self) -> None:
        """help_text в полях Post совпадает с ожидаемым."""
        data = {
            'group': 'Группа, к которой будет относиться пост',
            'text': 'Текст нового поста',
        }
        for field, expected in data.items():
            with self.subTest(field=field):
                testable = (
                    PostModelTest.post._meta.get_field(field).help_text)
                self.assertEqual(testable, expected)
