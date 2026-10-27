from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from .models import Post, Comment, Like
from .forms import PostForm, CommentForm

@login_required
def home_feed_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Your post is now live!")
            return redirect('home')
    else:
        form = PostForm()

    posts = Post.objects.select_related('author', 'author__profile')\
                        .prefetch_related('likes', 'comments__author', 'comments__author__profile')\
                        .all()

    # Precompute liked post IDs for current user to avoid n+1 queries
    user_liked_post_ids = set(Like.objects.filter(user=request.user, post__in=posts).values_list('post_id', flat=True))

    comment_form = CommentForm()

    context = {
        'form': form,
        'posts': posts,
        'user_liked_post_ids': user_liked_post_ids,
        'comment_form': comment_form,
    }
    return render(request, 'feed/home.html', context)

@login_required
def post_detail_view(request, pk):
    post = get_object_or_404(
        Post.objects.select_related('author', 'author__profile')
                    .prefetch_related('likes', 'comments__author', 'comments__author__profile'),
        pk=pk
    )
    user_has_liked = post.likes.filter(user=request.user).exists()
    comment_form = CommentForm()
    return render(request, 'feed/post_detail.html', {
        'post': post,
        'user_has_liked': user_has_liked,
        'comment_form': comment_form,
    })

@login_required
def post_edit_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return HttpResponseForbidden("You are not permitted to edit this post.")
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Post updated successfully.")
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'feed/post_edit.html', {'form': form, 'post': post})

@login_required
@require_POST
def post_delete_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return HttpResponseForbidden("You are not permitted to delete this post.")
    post.delete()
    messages.success(request, "Post has been deleted.")
    return redirect('home')

@login_required
@require_POST
def toggle_like_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like_obj = Like.objects.filter(user=request.user, post=post)
    
    if like_obj.exists():
        like_obj.delete()
        liked = False
    else:
        Like.objects.create(user=request.user, post=post)
        liked = True

    like_count = post.likes.count()
    return JsonResponse({
        'status': 'success',
        'liked': liked,
        'like_count': like_count
    })

@login_required
@require_POST
def add_comment_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()

        # Handle AJAX comment submission
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            avatar_url = comment.author.profile.avatar.url if comment.author.profile.avatar else ''
            return JsonResponse({
                'status': 'success',
                'comment': {
                    'id': comment.id,
                    'author': comment.author.username,
                    'avatar_url': avatar_url,
                    'content': comment.content,
                    'created_at': 'Just now',
                    'can_delete': True
                }
            })
        messages.success(request, "Comment published.")
        return redirect('post_detail', pk=pk)
    return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required
@require_POST
def delete_comment_view(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.author != request.user and comment.post.author != request.user:
        return HttpResponseForbidden("Not authorized to remove this comment.")
    post_pk = comment.post.pk
    comment.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    messages.success(request, "Comment removed.")
    return redirect('post_detail', pk=post_pk)

@login_required
def explore_view(request):
    q = request.GET.get('q', '').strip()
    users = []
    posts = Post.objects.select_related('author', 'author__profile').prefetch_related('likes', 'comments').all()
    if q:
        posts = posts.filter(content__icontains=q)
        users = User.objects.filter(username__icontains=q).exclude(id=request.user.id).select_related('profile')[:10]
    else:
        users = User.objects.exclude(id=request.user.id).select_related('profile').order_by('?')[:8]

    following_ids = set(request.user.following_set.values_list('following_id', flat=True))
    user_liked_post_ids = set(Like.objects.filter(user=request.user, post__in=posts).values_list('post_id', flat=True))

    return render(request, 'feed/explore.html', {
        'q': q,
        'posts': posts[:30],
        'users': users,
        'following_ids': following_ids,
        'user_liked_post_ids': user_liked_post_ids,
    })
