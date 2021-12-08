from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow

OUT_LIMIT = 10


def index(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, OUT_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'title': 'Последние обновления на сайте',
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all().order_by('-pub_date')
    paginator = Paginator(posts, OUT_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'title': f'Записи сообщества {group}',
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    if request.user.is_authenticated:
        user = get_object_or_404(User, username=username)
        posts = user.posts.all()
        count = posts.count()
        paginator = Paginator(posts, OUT_LIMIT)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        following = False
        filter_obj_st = Follow.objects.filter(user=request.user)
        if filter_obj_st.filter(author=user).exists():
            following = True
        context = {
            'author': user,
            'page_obj': page_obj,
            'title': f'Профайл пользователя {username}',
            'count': count,
            'following': following,
            'page_author': user
        }
        return render(request, 'posts/profile.html', context)
    else:
        user = get_object_or_404(User, username=username)
        posts = user.posts.all()
        count = posts.count()
        paginator = Paginator(posts, OUT_LIMIT)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {
            'author': user,
            'page_obj': page_obj,
            'title': f'Профайл пользователя {username}',
            'count': count,
            'page_author': user
        }
        return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    author = post.author
    count = author.posts.count()
    context = {
        'post': post,
        'count': count,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None,)
    if request.method == "POST":
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=post.author)

    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    instance = get_object_or_404(Post, id=post_id)
    if request.user != instance.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=instance,)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'post_id': post_id,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follows = request.user.follower.all()
    posts = []
    for follow in follows:
        posts = posts + list(Post.objects.filter(author=follow.author))
    paginator = Paginator(posts, OUT_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=request.user.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user).filter(author=author).delete()
    return redirect('posts:profile', username=request.user.username)
