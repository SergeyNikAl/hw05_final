from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from rest_framework.status import (
    HTTP_200_OK, HTTP_302_FOUND, HTTP_404_NOT_FOUND
)

from ..models import Group, Post, User

TEST_USERNAME = 'user'
TEST_AUTHOR_USERNAME = 'auth'
POST_TEST_TEXT = 'Текст поста'
GROUP_TEST_SLUG = 'test_slug'
GROUP_TEST_TITLE = 'Заголовок'

INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:create_post')
LOGIN_URL = reverse('users:login')
PROFILE_URL = reverse(
    'posts:profile', kwargs={'username': TEST_AUTHOR_USERNAME}
)
GROUP_POSTS_URL = reverse(
    'posts:group_list', kwargs={'slug': GROUP_TEST_SLUG}
)
FOLLOW_URL = reverse('posts:follow_index')
FOLLOWING_URL = reverse(
    'posts:profile_follow',
    kwargs={'username': TEST_AUTHOR_USERNAME}
)
UNFOLLOW_URL = reverse(
    'posts:profile_unfollow',
    kwargs={'username': TEST_AUTHOR_USERNAME}
)
UNEXISTING_PAGE = "/unexisting_page/"


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_AUTHOR_USERNAME)
        cls.authorized_user = User.objects.create_user(username=TEST_USERNAME)
        cls.post = Post.objects.create(
            text=POST_TEST_TEXT,
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title=GROUP_TEST_TITLE,
            slug=GROUP_TEST_SLUG,
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.id}
        )

        cls.guest = Client()
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.another = Client()
        cls.another.force_login(cls.authorized_user)

    def setUp(self):
        cache.clear()

    def test_added_url_uses_correct_template(self):
        """Страницы вызываются по ожидаемому HTML-адресу."""
        templates_urls = {
            INDEX_URL: 'posts/index.html',
            GROUP_POSTS_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            self.POST_DETAIL_URL: 'posts/post_detail.html',
            POST_CREATE_URL: 'posts/create_post.html',
            self.POST_EDIT_URL: 'posts/create_post.html',
            FOLLOW_URL: 'posts/follow.html'
        }

        for address, template in templates_urls.items():
            with self.subTest(address=address, template=template):
                self.assertTemplateUsed(
                    self.author.get(address), template
                )

    def test_post_list_url_exists_at_desired_location_for_all(self):
        """Тест доступности страницы по ожидаемому адресу."""
        pages_status = [
            [INDEX_URL, self.guest, HTTP_200_OK],
            [GROUP_POSTS_URL, self.guest, HTTP_200_OK],
            [PROFILE_URL, self.guest, HTTP_200_OK],
            [self.POST_DETAIL_URL, self.guest, HTTP_200_OK],
            [POST_CREATE_URL, self.guest, HTTP_302_FOUND],
            [self.POST_EDIT_URL, self.guest, HTTP_302_FOUND],
            [POST_CREATE_URL, self.another, HTTP_200_OK],
            [self.POST_EDIT_URL, self.another, HTTP_302_FOUND],
            [self.POST_EDIT_URL, self.author, HTTP_200_OK],
            [FOLLOW_URL, self.guest, HTTP_302_FOUND],
            [FOLLOW_URL, self.another, HTTP_200_OK],
            [FOLLOWING_URL, self.guest, HTTP_302_FOUND],
            [FOLLOWING_URL, self.another, HTTP_302_FOUND],
            [FOLLOWING_URL, self.author, HTTP_302_FOUND],
            [UNFOLLOW_URL, self.guest, HTTP_302_FOUND],
            [UNFOLLOW_URL, self.another, HTTP_302_FOUND],
            [UNEXISTING_PAGE, self.author, HTTP_404_NOT_FOUND]
        ]
        for address, client, code in pages_status:
            with self.subTest(address=address, client=client):
                self.assertEqual(
                    client.get(address).status_code, code
                )

    def test_post_redirect_urls(self):
        """Проверка перенаправления."""

        pages_redirect = [
            [POST_CREATE_URL,
             self.guest,
             f'{LOGIN_URL}?next={POST_CREATE_URL}'],
            [self.POST_EDIT_URL,
             self.guest,
             f'{LOGIN_URL}?next={self.POST_EDIT_URL}'],
            [FOLLOW_URL, self.guest, f'{LOGIN_URL}?next={FOLLOW_URL}'],
            [FOLLOWING_URL, self.guest, f'{LOGIN_URL}?next={FOLLOWING_URL}'],
            [UNFOLLOW_URL, self.guest, f'{LOGIN_URL}?next={UNFOLLOW_URL}'],
            [self.POST_EDIT_URL, self.another, self.POST_DETAIL_URL],
            [FOLLOWING_URL, self.another, PROFILE_URL],
            [UNFOLLOW_URL, self.another, PROFILE_URL],
            [FOLLOWING_URL, self.author, PROFILE_URL],
        ]

        for address, client, redirect in pages_redirect:
            with self.subTest(address=address, redirect=redirect):
                self.assertRedirects(
                    client.get(address, follow=True), redirect
                )
