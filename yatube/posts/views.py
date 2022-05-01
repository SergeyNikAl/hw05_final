from django.core.paginator import Paginator
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Post, Group, User, Follow


def get_page(request, posts: QuerySet):
    return Paginator(posts, settings.POSTS_ON_PAGES).get_page(
        request.GET.get('page')
    )


def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': get_page(request, Post.objects.all())
    })


def group_posts_list(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': get_page(request, group.posts.all()),
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    follow = (request.user.is_authenticated
              and request.user.username != username
              and Follow.objects.filter(author=author,
                                        user=request.user).exists())
    return render(request, 'posts/profile.html', {
        'author': author,
        'page_obj': get_page(request, author.posts.all()),
        'following': follow
    })


def post_detail(request, post_id):
    return render(request, 'posts/post_detail.html', {
        'post': get_object_or_404(Post, id=post_id),
        'form': CommentForm(),
    })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'form': form,
        })
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=request.user.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html', {
        'form': form,
        'post': post,
    })


@login_required
def follow_index(request):
    return render(request, 'posts/follow.html', {
        'page_obj': get_page(
            request, Post.objects.filter(
                author__following__user=request.user
            )
        )
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user.username == username:
        return redirect('posts:profile', username=username)
    Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow, user=request.user, author__username=username
    ).delete()
    return redirect('posts:profile', username=username)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author and request.method != 'POST':
        return redirect('posts:post_detail', post_id)
    post.delete()
    return redirect('posts:profile', post.author)
