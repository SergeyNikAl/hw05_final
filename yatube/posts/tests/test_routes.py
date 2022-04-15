from django.test import TestCase
from django.urls import reverse

from ..urls import app_name

ID = 1
USERNAME = 'test_user'
SLUG = 'test_slug'

ROUTES_DATA = [
    ['/', 'index', []],
    [f'/group/{SLUG}/', 'group_list', [SLUG]],
    [f'/profile/{USERNAME}/', 'profile', [USERNAME]],
    [f'/posts/{ID}/', 'post_detail', [ID]],
    [f'/posts/{ID}/edit/', 'post_edit', [ID]],
    ['/create/', 'create_post', []],
    [f'/profile/{USERNAME}/follow/', 'profile_follow', [USERNAME]],
    [f'/profile/{USERNAME}/unfollow/', 'profile_unfollow', [USERNAME]],
]


class TestRoutesUrls(TestCase):

    def test_routes(self):
        for url, route, args in ROUTES_DATA:
            with self.subTest(url=url, route=route, args=args):
                urls = reverse(f'{app_name}:{route}', args=args)
                self.assertEqual(url, urls)
