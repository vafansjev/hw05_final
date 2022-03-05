# -*- coding: cp1251 -*-
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm

POSTS_PER_PAGE = 10


def paginate_in_view(queryset, request):
    page_number = request.GET.get('page')
    paginator = Paginator(queryset, POSTS_PER_PAGE)
    page_obj = paginator.get_page(page_number)

    return {
        'page_obj': page_obj,
        'post_count': queryset.count()
    }


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    pagination_context = paginate_in_view(
        posts,
        request,
    )
    title = 'Последние обновления на сайте'
    context = {
        'page_obj': pagination_context['page_obj'],
        'title': title,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    pagination_context = paginate_in_view(
        posts,
        request,
    )
    context = {
        'group': group,
        'page_obj': pagination_context['page_obj'],
        'group.title': group.title,
        'group.description': group.description,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    following = False
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author_id=user.id)
    pagination_context = paginate_in_view(
        posts,
        request,
    )
    title = 'Профайл пользователя'

    if request.user.is_authenticated:
        followers = Follow.objects.filter(
            author_id=user.id, user_id=request.user)
        if followers:
            following = True

    context = {
        'page_obj': pagination_context['page_obj'],
        'title': title,
        'post_count': pagination_context['post_count'],
        'username': user,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = Post.objects.get(pk=post_id)
    form = CommentForm()
    comment = post.comments.all()
    posts_count = Post.objects.filter(author=post.author).count()
    title = post.text[0:30]
    context = {
        'post': post,
        'title': title,
        'posts_count': posts_count,
        'form': form,
        'comments': comment,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    context = {
        'form': form,
    }
    if not form.is_valid():
        return render(request, template, context)
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    template = 'posts/create_post.html'
    return_view = 'posts:post_detail'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    is_edit = True
    context = {
        'form': form,
        'is_edit': is_edit,
        'post_id': post_id,
    }
    if not request.user == post.author:
        return redirect(return_view, post_id=post.pk)
    if not form.is_valid():
        return render(request, template, context)
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect(return_view, post_id=post.pk)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    title = 'Мои подписки'
    authors = Follow.objects.filter(user=request.user).values_list(
        'author_id', flat=True
    )
    posts = Post.objects.filter(author_id__in=authors)
    pagination_context = paginate_in_view(
        posts,
        request,
    )

    context = {
        'page_obj': pagination_context['page_obj'],
        'title': title,
        'post_count': pagination_context['post_count'],
    }

    return render(request, template, context)


@login_required
def profile_follow(request, username):
    following = get_object_or_404(User, username=username)
    current_user = request.user
    if current_user != following:
        Follow.objects.get_or_create(user=current_user, author=following)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    current_user = request.user
    following = get_object_or_404(User, username=username)
    Follow.objects.filter(author=following, user=current_user).delete()
    return redirect('posts:profile', username=username)
