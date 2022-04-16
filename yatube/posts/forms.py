from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст',
            'group': 'Выберите группу',
            'image': 'Картинка'
        }
        help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа поста',
            'image': 'Выберите картинку для поста',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария',
        }
        help_texts = {
            'text': 'Введите текст комментария',
        }
