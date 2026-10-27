from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import UserRegistrationForm, UserUpdateForm, ProfileUpdateForm
from .models import Follow, Profile

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            messages.success(request, f"Welcome to Connectly, @{user.username}!")
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(User.objects.select_related('profile'), username=username)
    posts = profile_user.posts.all().select_related('author', 'author__profile').prefetch_related('likes', 'comments').order_by('-created_at')
    
    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
    
    followers_count = profile_user.followers_set.count()
    following_count = profile_user.following_set.count()

    context = {
        'profile_user': profile_user,
        'posts': posts,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect('profile', username=request.user.username)
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'accounts/edit_profile.html', {'u_form': u_form, 'p_form': p_form})

@login_required
@require_POST
def toggle_follow_view(request, username):
    target_user = get_object_or_404(User, username=username)
    if request.user == target_user:
        return JsonResponse({'error': 'Cannot follow yourself'}, status=400)

    follow_rel = Follow.objects.filter(follower=request.user, following=target_user)
    if follow_rel.exists():
        follow_rel.delete()
        following = False
    else:
        Follow.objects.create(follower=request.user, following=target_user)
        following = True

    followers_count = target_user.followers_set.count()
    return JsonResponse({
        'status': 'success',
        'following': following,
        'followers_count': followers_count
    })

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')
