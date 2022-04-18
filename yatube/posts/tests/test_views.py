import shutil
import tempfile

from django.test import Client, TestCase
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.urls import reverse

from ..models import Group, Post, User, Follow

TEST_USERNAME = 'user'
TEST_AUTHOR_USERNAME = 'auth'
POST_TEST_TEXT = 'Текст поста'
GROUP_TEST_SLUG = 'test_slug'
GROUP_TEST_TITLE = 'Заголовок'
GROUP_2_TEST_SLUG = 'test_slug_2'
GROUP_2_TEST_TITLE = 'Заголовок_2'
DESCRIPTION = 'Описание группы'
DESCRIPTION_2 = 'Описание группы 2'
NEXT_PAGE = '?page=2'
POSTS_ON_PAGE_2 = 3

INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:create_post')
PROFILE_URL = reverse(
    'posts:profile', kwargs={'username': TEST_AUTHOR_USERNAME}
)
GROUP_POSTS_URL = reverse(
    'posts:group_list', kwargs={'slug': GROUP_TEST_SLUG}
)
GROUP_2_POSTS_URL = reverse(
    'posts:group_list', kwargs={'slug': GROUP_2_TEST_SLUG}
)
INDEX_FOLLOW_URL = reverse('posts:follow_index')
FOLLOW_URL = reverse(
    'posts:profile_follow',
    kwargs={'username': TEST_AUTHOR_USERNAME}
)
UNFOLLOW_URL = reverse(
    'posts:profile_unfollow',
    kwargs={'username': TEST_AUTHOR_USERNAME}
)
PAGES_URL = [
    [INDEX_URL, settings.POSTS_ON_PAGES],
    [PROFILE_URL, settings.POSTS_ON_PAGES],
    [GROUP_POSTS_URL, settings.POSTS_ON_PAGES],
    [INDEX_FOLLOW_URL, settings.POSTS_ON_PAGES],
    [INDEX_URL + NEXT_PAGE, POSTS_ON_PAGE_2],
    [PROFILE_URL + NEXT_PAGE, POSTS_ON_PAGE_2],
    [GROUP_POSTS_URL + NEXT_PAGE, POSTS_ON_PAGE_2],
    [INDEX_FOLLOW_URL + NEXT_PAGE, POSTS_ON_PAGE_2],
]
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


class TestViewClass(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_AUTHOR_USERNAME)
        cls.authorized_user = User.objects.create_user(username=TEST_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TEST_TITLE,
            slug=GROUP_TEST_SLUG,
            description=DESCRIPTION
        )
        cls.group_2 = Group.objects.create(
            title=GROUP_2_TEST_TITLE,
            slug=GROUP_2_TEST_SLUG,
            description=DESCRIPTION_2
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text=POST_TEST_TEXT,
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )
        cls.follow = Follow.objects.create(
            author=cls.user,
            user=cls.authorized_user,
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

        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_show_correct_context(self):
        """Страницы сформированы с корректным контекстом"""
        url_pages = [
            INDEX_URL,
            GROUP_POSTS_URL,
            PROFILE_URL,
            self.POST_DETAIL_URL,
            INDEX_FOLLOW_URL,
        ]
        for url in url_pages:
            with self.subTest(url=url):
                response = self.another.get(url)
                if 'page_obj' in response.context:
                    self.assertEqual(len(response.context['page_obj']), 1)
                    post = response.context['page_obj'][0]
                else:
                    post = response.context['post']
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(post.image, self.post.image)

    def test_profile_context(self):
        """Страница профиля сформирована с корректным контекстом"""
        self.assertEqual(
            self.guest.get(PROFILE_URL).context['author'],
            self.user
        )

    def test_additional_context_group(self):
        """Страница группы сформирована с корректным контекстом"""
        response = self.guest.get(GROUP_POSTS_URL)
        group = response.context['group']
        self.assertEqual(group, self.group)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)

    def test_new_post_in_another_group(self):
        """Наличие поста в другой группе"""
        self.assertNotIn(
            self.post,
            self.another.get(GROUP_2_POSTS_URL).context['page_obj']
        )

    def test_paginator_on_pages(self):
        """Тест количества постов на страницах"""
        Post.objects.all().delete()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        Post.objects.bulk_create(
            Post(
                text=f'Пост {number}',
                author=self.user,
                group=self.group,
                image=uploaded)
            for number in range(settings.POSTS_ON_PAGES + POSTS_ON_PAGE_2)
        )
        cache.clear()
        for url, posts_count in PAGES_URL:
            with self.subTest(url=url):
                response = self.another.get(url)
                self.assertEqual(
                    len(response.context['page_obj']),
                    posts_count
                )

    def test_post_following_author(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто не подписан на него."""
        response = self.another.get(INDEX_FOLLOW_URL)
        self.assertTrue(len(response.context['page_obj']), 0)

    def test_follow(self):
        """Тест подписки на автора"""
        Follow.objects.all().delete()
        follow = self.another.get(FOLLOW_URL)
        exist_follow = Follow.objects.filter(
            user=self.authorized_user,
            author=self.user
        )
        self.assertTrue(exist_follow, follow)

    def test_unfollow(self):
        """Тест подписки на автора"""
        self.another.get(UNFOLLOW_URL)
        self.assertFalse(
            Follow.objects.filter(
                user=self.authorized_user, author=self.user
            ).exists()
        )
