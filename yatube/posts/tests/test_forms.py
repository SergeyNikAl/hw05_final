import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.conf import settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEST_AUTHOR_USERNAME = 'auth'
TEST_USERNAME = 'user'
POST_TEST_TEXT = 'Текст поста'
GROUP_TEST_SLUG = 'test_slug'
GROUP_TEST_TITLE = 'Заголовок'
GROUP_2_TEST_SLUG = 'test_slug_2'
GROUP_2_TEST_TITLE = 'Заголовок_2'
DESCRIPTION = 'Описание группы'
DESCRIPTION_2 = 'Описание группы 2'
POST_CREATE_URL = reverse('posts:create_post')
PROFILE_URL = reverse(
    'posts:profile', kwargs={'username': TEST_AUTHOR_USERNAME}
)
LOGIN_URL = reverse('users:login')
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


class TestFormClass(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_AUTHOR_USERNAME)
        cls.another_user = User.objects.create_user(username=TEST_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TEST_TITLE,
            slug=GROUP_TEST_SLUG,
            description=DESCRIPTION
        )
        cls.group_1 = Group.objects.create(
            title=GROUP_2_TEST_TITLE,
            slug=GROUP_2_TEST_SLUG,
            description=DESCRIPTION_2
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEST_TEXT,
            group=cls.group
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail', kwargs={
            'post_id': cls.post.id})
        cls.POST_EDIT_URL = reverse('posts:post_edit', kwargs={
            'post_id': cls.post.id})
        cls.ADD_COMMENT_URL = reverse('posts:add_comment', kwargs={
            'post_id': cls.post.id
        })

        cls.guest = Client()
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.another = Client()
        cls.another.force_login(cls.another_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        Post.objects.all().delete()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'new_text',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.author.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.get()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.user)
        self.assertTrue(
            str(form_data['image']).split('.')[0] in str(post.image.file)
        )
        self.assertRedirects(response, PROFILE_URL)

    def test_edit_post(self):
        """Валидная форма редактирования записи Post."""
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый текст поста',
            'group': self.group_1.id,
            'image': uploaded,
        }
        response = self.author.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        post = response.context.get('post')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.post.author)
        self.assertTrue(
            str(form_data['image']).split('.')[0] in str(post.image.file)
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)

    def test_guest_create_comment(self):
        """Анонимный пользователь не может оставлять комментарии."""
        Comment.objects.all().delete()
        form_data = {
            'text': 'new_text',
        }
        response = self.guest.post(
            self.ADD_COMMENT_URL,
            data=form_data,
        )
        self.assertEqual(Comment.objects.count(), 0)
        self.assertRedirects(
            response,
            f'{LOGIN_URL}?next={self.ADD_COMMENT_URL}'
        )

    def test_create_comment(self):
        """Валидная форма создает комментарий к Post."""
        Comment.objects.all().delete()
        form_data = {
            'text': 'new_text',
        }
        response = self.another.post(
            self.ADD_COMMENT_URL,
            data=form_data,
        )
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.get()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.another_user)
        self.assertRedirects(response, self.POST_DETAIL_URL)
