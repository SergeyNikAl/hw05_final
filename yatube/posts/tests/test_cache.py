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
            username=TEST_AUTHOR_USERNAME)
        self.author = Client()
        self.author.force_login(self.user)

    def test_index_cache(self):
        """Проверка кэширования главной страницы"""
        Post.objects.all().delete()
        response_1 = self.author.get(INDEX_URL)
        self.post = Post.objects.create(
            text=POST_TEST_TEXT,
            author=self.user
        )
        response_2 = self.author.get(INDEX_URL)
        Post.objects.all().delete()
        response_3 = self.author.get(INDEX_URL)
        cache.clear()
        response_4 = self.author.get(INDEX_URL)
        self.assertEqual(response_2.content, response_3.content)
        self.assertEqual(response_1.content, response_4.content)
