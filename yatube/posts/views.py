from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import post_obj

COUNT_POST_ON_PAGE: int = 10


def index(request):
    """Главная страница."""
    post_list = Post.objects.select_related('group', 'author')
    context = {
        'page_obj': post_obj(request, post_list, COUNT_POST_ON_PAGE),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Посты группы."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('group', 'author')
    context = {
        'group': group,
        'page_obj': post_obj(request, post_list, COUNT_POST_ON_PAGE),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Посты автора."""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group', 'author')
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author).exists()
    else:
        following = False
    context = {
        'author': author,
        'page_obj': post_obj(request, post_list, COUNT_POST_ON_PAGE),
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница поста."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comments = post.comments.select_related('author')
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Новый пост создать."""
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    context = {'form': form}
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    """Редактировать пост."""
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)

    context = {
        'form': form,
        'is_edit': True,
        'author': post.author,
        'user': request.user,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """Комментировать пост."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect(comment)


@login_required
def follow_index(request):
    """Лента подписок."""
    post_list = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': post_obj(request, post_list, COUNT_POST_ON_PAGE),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора."""
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Отписаться от автора."""
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user=request.user,
                             author=author).exists():
        unfollow = Follow.objects.get(user=request.user,
                                      author=author)
        unfollow.delete()
    return redirect('posts:profile', username)
