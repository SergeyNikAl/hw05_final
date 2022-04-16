from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, User

INDEX_URL = reverse('posts:index')
TEST_AUTHOR_USERNAME = 'USERNAME'
POST_TEST_TEXT = 'Текст поста'


class TestCache(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username=TEST_AUTHOR_USERNAME
        )
        self.author = Client()
        self.author.force_login(self.user)
        self.post = Post.objects.create(
            text=POST_TEST_TEXT,
            author=self.user,
        )

    def test_index_cache(self):
        """Проверка кэширования главной страницы"""
        content = self.client.get(INDEX_URL).content
        Post.objects.all().delete()
        self.assertEqual(content, Client().get(INDEX_URL).content)
        cache.clear()
        self.assertNotEqual(content, Client().get(INDEX_URL).content)
