from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import RegisterForm, LoginForm
from .models import User, Follow


def register_view(request):
    if request.user.is_authenticated:
        return redirect("users:home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to Sphere, {user.display_name}! 🎉")
            return redirect("users:home")
        else:
            messages.error(request, "Please fix the errors below.")
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("users:home")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            login(request, form.get_user())
            return redirect(request.GET.get("next", "") or "users:home")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("users:login")


@login_required
def home(request):
    from stories.views import get_story_authors_for_user

    following_ids = Follow.objects.filter(
        follower=request.user
    ).values_list("following_id", flat=True)

    following_users = User.objects.filter(id__in=following_ids)

    suggestions = User.objects.exclude(
        id__in=list(following_ids)
    ).exclude(id=request.user.id).order_by("?")[:20]

    story_authors = get_story_authors_for_user(request.user)

    return render(request, "users/home.html", {
        "following_users": following_users,
        "suggestions":     suggestions,
        "story_authors":   story_authors,
    })


@login_required
def follow_toggle(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return redirect("users:home")
    existing = Follow.objects.filter(follower=request.user, following=target)
    if existing.exists():
        existing.delete()
    else:
        Follow.objects.create(follower=request.user, following=target)
    return redirect(request.META.get("HTTP_REFERER", "/users/home/"))


@login_required
def search_view(request):
    query = request.GET.get("q", "").strip()
    results = []
    if query:
        results = User.objects.filter(
            Q(username__icontains=query) | Q(display_name__icontains=query)
        ).exclude(id=request.user.id)
    return render(request, "users/search.html", {"results": results, "query": query})