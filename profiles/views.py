from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from users.models import User, Follow


@login_required
def profile_view(request, username=None):
    profile_user = request.user if username is None else get_object_or_404(User, username=username)
    is_own = profile_user == request.user
    is_following = False

    if not is_own:
        is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()

    followers = Follow.objects.filter(following=profile_user).select_related("follower")
    following = Follow.objects.filter(follower=profile_user).select_related("following")

    return render(request, "profiles/profile.html", {
        "profile_user": profile_user,
        "is_own": is_own,
        "is_following": is_following,
        "followers": followers,
        "following": following,
    })


@login_required
def profile_edit_view(request):
    if request.method == "POST":
        user = request.user
        user.display_name = request.POST.get("display_name", "").strip() or user.username
        user.bio = request.POST.get("bio", "").strip()
        if "profile_picture" in request.FILES:
            user.profile_picture = request.FILES["profile_picture"]
        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("profiles:edit")

    return render(request, "users/profile_edit.html", {"user": request.user})
