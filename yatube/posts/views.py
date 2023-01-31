from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from yatube.settings import NUM_OF_POSTS
from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    paginator = Paginator(posts, NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    paginator = Paginator(posts, NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = author.following.exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(data=request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(data=request.POST)
    if request.method != 'POST':
        form = PostForm(request.POST or None)
        return render(request, 'posts/create_post.html', {'form': form})
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', post.author)


@login_required
def post_edit(request, post_id):
    is_edit = get_object_or_404(Post, pk=post_id)
    if is_edit.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=is_edit
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': is_edit,
        'form': form,
        'is_edit': True,
        'post_id': post_id
    }
    return render(request, 'posts/create_post.html', context)


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
    follower = Follow.objects.filter(user=request.user).values_list(
        'author_id',
    )
    posts = Post.objects.filter(author_id__in=follower)
    paginator = Paginator(posts, NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.get(user=request.user, author=author).delete()
    return redirect('posts:follow_index')
