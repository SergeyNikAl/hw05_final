from django.test import Client, TestCase
from django.urls import reverse

from users.forms import CreationForm, User

INDEX_URL = reverse('posts:index')
SIGN_UP_URL = reverse('users:signup')


class CreationFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create()
        cls.form = CreationForm()

    def setUp(self):
        self.guest = Client()

    def test_creation_new_user(self):
        """Валидная форма создает нового пользователя."""
        form_data = {
            "first_name": "Serg",
            "last_name": "Nik",
            "username": "SergNik",
            "email": "SergNik@yatube.ru",
            "password1": "Django_2022",
            "password2": "Django_2022",
        }
        existing_users = set(User.objects.all())
        response = self.guest.post(
            SIGN_UP_URL,
            data=form_data,
            follow=True
        )
        existing_users = set(User.objects.all()) - existing_users
        self.assertEqual(len(existing_users), 1)
        new_user = existing_users.pop()
        self.assertEqual(new_user.first_name, form_data['first_name'])
        self.assertEqual(new_user.last_name, form_data['last_name'])
        self.assertEqual(new_user.username, form_data['username'])
        self.assertEqual(new_user.email, form_data['email'])
        self.assertRedirects(response, INDEX_URL)
