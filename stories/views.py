import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from users.models import User, Follow
from .models import Story


# ──────────────────────────────────────────────
# HOME FEED: who has active stories?
# Called by home_view to pass story rings data
# ──────────────────────────────────────────────
def get_story_authors_for_user(current_user):
    """
    Returns an ordered list of dicts:
      { user, stories: [...], has_unseen: bool, is_self: bool }

    Order: self first, then following — sorted by latest story.
    """
    following_ids = list(
        Follow.objects.filter(follower=current_user)
        .values_list("following_id", flat=True)
    )

    # Gather all authors (self + following) who have active stories
    active_now = timezone.now()
    author_ids_with_stories = (
        Story.objects
        .filter(author_id__in=[current_user.pk] + following_ids, expires_at__gt=active_now)
        .values_list("author_id", flat=True)
        .distinct()
    )

    result = []
    for uid in author_ids_with_stories:
        author = User.objects.get(pk=uid)
        stories = list(
            Story.objects.filter(author=author, expires_at__gt=active_now)
            .order_by("created_at")
        )
        has_unseen = any(current_user not in s.viewers.all() for s in stories)
        result.append({
            "user":       author,
            "stories":    stories,
            "has_unseen": has_unseen,
            "is_self":    author == current_user,
        })

    # Self first, then by latest story upload descending
    result.sort(key=lambda x: (not x["is_self"], -x["stories"][-1].created_at.timestamp()))
    return result


# ──────────────────────────────────────────────
# UPLOAD PAGE
# ──────────────────────────────────────────────
@login_required
def upload_story(request):
    return render(request, "stories/upload.html")


# ──────────────────────────────────────────────
# SAVE (AJAX POST from the editor)
# ──────────────────────────────────────────────
@login_required
@require_POST
def save_story(request):
    media_file = request.FILES.get("media_file")
    audio_file = request.FILES.get("audio_file")

    if not media_file:
        return JsonResponse({"error": "No file."}, status=400)

    media_type = "video" if media_file.content_type.startswith("video") else "image"

    Story.objects.create(
        author     = request.user,
        media_type = media_type,
        media_file = media_file,
        audio_file = audio_file or None,
        caption    = request.POST.get("caption", "")[:200],
        trim_start = float(request.POST.get("trim_start", 0)),
        trim_end   = float(request.POST.get("trim_end", 0)),
    )
    return JsonResponse({"ok": True, "redirect": "/users"})


# ──────────────────────────────────────────────
# VIEWER — GET /stories/<username>/
# Returns the full story list for that author
# JS plays them locally, no further requests
# ──────────────────────────────────────────────
@login_required
def story_viewer(request, username):
    author = get_object_or_404(User, username=username)
    active_now = timezone.now()

    # Only followers (or self) can view
    if author != request.user:
        can_view = Follow.objects.filter(
            follower=request.user, following=author
        ).exists()
        if not can_view:
            return redirect("users:home")

    stories = Story.objects.filter(
        author=author,
        expires_at__gt=active_now
    ).order_by("created_at")

    if not stories.exists():
        return redirect("users:home")

    # Serialise all stories for the JS player
    stories_data = []
    for s in stories:
        stories_data.append({
            "id":         s.pk,
            "media_type": s.media_type,
            "media_url":  s.media_file.url,
            "audio_url":  s.audio_file.url if s.audio_file else None,
            "caption":    s.caption,
            "trim_start": s.trim_start,
            "trim_end":   s.trim_end,
            "seen":       request.user in s.viewers.all(),
        })

    return render(request, "stories/viewer.html", {
        "author":       author,
        "stories_json": json.dumps(stories_data),
        "story_count":  stories.count(),
    })


# ──────────────────────────────────────────────
# MARK AS VIEWED (called by JS per story)
# ──────────────────────────────────────────────
@login_required
@require_POST
def mark_viewed(request, story_id):
    story = get_object_or_404(Story, pk=story_id)
    story.viewers.add(request.user)
    return JsonResponse({"ok": True})


# ──────────────────────────────────────────────
# DELETE (own story only)
# ──────────────────────────────────────────────
@login_required
@require_POST
def delete_story(request, story_id):
    story = get_object_or_404(Story, pk=story_id, author=request.user)
    story.media_file.delete(save=False)
    if story.audio_file:
        story.audio_file.delete(save=False)
    story.delete()
    return JsonResponse({"ok": True})