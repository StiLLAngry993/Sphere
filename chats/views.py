from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import (
    Conversation, ConversationMember,
    Message, Attachment, MessageReaction, ReadReceipt
)

User = get_user_model()


# ── helpers ────────────────────────────────────────────────

def get_or_create_dm(user_a, user_b):
    """
    Find existing DM between two users or create one.
    This is how Instagram/Messenger works:
      - Search user → click Chat → open (or create) the conversation
    """
    # Find a non-group conversation both users are in
    shared = (
        Conversation.objects
        .filter(is_group=False, members__user=user_a)
        .filter(members__user=user_b)
    )
    if shared.exists():
        return shared.first(), False

    # None found — create it
    conv = Conversation.objects.create(is_group=False)
    ConversationMember.objects.create(conversation=conv, user=user_a, is_admin=True)
    ConversationMember.objects.create(conversation=conv, user=user_b)
    return conv, True


def mark_messages_read(conversation, user):
    """Mark all unread messages in this conversation as read for this user."""
    unread = conversation.messages.filter(
        deleted=False
    ).exclude(sender=user).exclude(read_receipts__user=user)

    receipts = [
        ReadReceipt(message=msg, user=user)
        for msg in unread
    ]
    ReadReceipt.objects.bulk_create(receipts, ignore_conflicts=True)


# ── Phase 4: Conversation list ─────────────────────────────

@login_required
def inbox(request):
    """
    Show all conversations the current user is part of,
    ordered by most recent activity.
    """
    memberships = (
        ConversationMember.objects
        .filter(user=request.user)
        .select_related("conversation")
        .order_by("-conversation__updated_at")
    )

    conversations = []
    for m in memberships:
        conv = m.conversation
        last = conv.last_message()
        other = conv.get_other_member(request.user) if not conv.is_group else None
        conversations.append({
            "conv":        conv,
            "last_msg":    last,
            "other":       other,
            "unread":      conv.unread_count(request.user),
            "is_muted":    m.is_muted,
        })

    return render(request, "chats/inbox.html", {
        "conversations": conversations,
    })


# ── Phase 4: Start or open a DM ───────────────────────────

@login_required
def start_dm(request, username):
    """
    Called when user clicks 'Chat' on someone's profile or search result.
    Creates DM if needed, then opens it.
    """
    other_user = get_object_or_404(User, username=username)

    if other_user == request.user:
        return redirect("chats:inbox")

    conv, _ = get_or_create_dm(request.user, other_user)
    return redirect("chats:room", pk=conv.pk)


# ── Phase 4 + 5: Open conversation room ───────────────────

@login_required
def room(request, pk):
    """
    Open a conversation.
    - Verifies user is a member.
    - Loads all messages.
    - Marks everything as read.
    - Phase 5: handles POST to send a message.
    """
    conv = get_object_or_404(Conversation, pk=pk)

    # Security: must be a member
    membership = ConversationMember.objects.filter(
        conversation=conv, user=request.user
    ).first()
    if not membership:
        return redirect("chats:inbox")

    # Phase 5 — send message (POST)
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        reply_to_id = request.POST.get("reply_to")
        reply_to = None

        if reply_to_id:
            try:
                reply_to = Message.objects.get(
                    pk=reply_to_id, conversation=conv, deleted=False
                )
            except Message.DoesNotExist:
                pass

        if text:
            msg = Message.objects.create(
                conversation=conv,
                sender=request.user,
                text=text,
                reply_to=reply_to,
            )
            # Handle file attachments
            for f in request.FILES.getlist("files"):
                ct = f.content_type
                if ct.startswith("image"):
                    ftype = "image"
                elif ct.startswith("video"):
                    ftype = "video"
                elif ct.startswith("audio"):
                    ftype = "audio"
                else:
                    ftype = "file"
                Attachment.objects.create(
                    message=msg,
                    file_type=ftype,
                    file=f,
                    file_name=f.name,
                    file_size=f.size,
                )

            # Bump conversation updated_at so it rises to the top
            conv.save(update_fields=["updated_at"])

        return redirect("chats:room", pk=pk)

    # GET — load messages
    messages_qs = (
        conv.messages
        .filter(deleted=False)
        .select_related("sender", "reply_to", "reply_to__sender")
        .prefetch_related("attachments", "reactions", "read_receipts__user")
        .order_by("created_at")
    )

    # Mark all as read
    mark_messages_read(conv, request.user)

    # Group info for the template
    other = conv.get_other_member(request.user) if not conv.is_group else None
    members = conv.members.select_related("user").all()

    return render(request, "chats/room.html", {
        "conv":       conv,
        "messages":   messages_qs,
        "other":      other,
        "members":    members,
        "membership": membership,
    })


# ── Create group chat ──────────────────────────────────────

@login_required
def create_group(request):
    if request.method == "POST":
        name = request.POST.get("group_name", "").strip()
        member_ids = request.POST.getlist("members")

        if not name:
            return redirect("chats:inbox")

        conv = Conversation.objects.create(is_group=True, group_name=name)

        if "group_image" in request.FILES:
            conv.group_image = request.FILES["group_image"]
            conv.save()

        # Add creator as admin
        ConversationMember.objects.create(
            conversation=conv, user=request.user, is_admin=True
        )
        # Add selected members
        for uid in member_ids:
            try:
                u = User.objects.get(pk=uid)
                if u != request.user:
                    ConversationMember.objects.create(conversation=conv, user=u)
            except User.DoesNotExist:
                pass

        return redirect("chats:room", pk=conv.pk)

    # GET — show form
    from users.models import Follow
    following = User.objects.filter(
        id__in=Follow.objects.filter(follower=request.user).values_list("following_id", flat=True)
    )
    return render(request, "chats/create_group.html", {"following": following})


# ── Phase 7 previews: react, edit, delete ─────────────────

@login_required
@require_POST
def react(request, msg_id):
    msg   = get_object_or_404(Message, pk=msg_id, deleted=False)
    emoji = request.POST.get("emoji", "").strip()
    if not emoji:
        return JsonResponse({"error": "No emoji"}, status=400)

    reaction, created = MessageReaction.objects.get_or_create(
        message=msg, user=request.user, emoji=emoji
    )
    if not created:
        reaction.delete()
        return JsonResponse({"ok": True, "action": "removed"})
    return JsonResponse({"ok": True, "action": "added"})


@login_required
@require_POST
def edit_message(request, msg_id):
    msg  = get_object_or_404(Message, pk=msg_id, sender=request.user, deleted=False)
    text = request.POST.get("text", "").strip()
    if not text:
        return JsonResponse({"error": "Empty"}, status=400)
    msg.text      = text
    msg.edited    = True
    msg.edited_at = timezone.now()
    msg.save(update_fields=["text", "edited", "edited_at"])
    return JsonResponse({"ok": True, "text": msg.text})


@login_required
@require_POST
def delete_message(request, msg_id):
    msg = get_object_or_404(Message, pk=msg_id, sender=request.user)
    msg.deleted    = True
    msg.deleted_at = timezone.now()
    msg.save(update_fields=["deleted", "deleted_at"])
    return JsonResponse({"ok": True})


@login_required
@require_POST
def send_gif(request, pk):
    """Send a Giphy GIF into a conversation."""
    conv = get_object_or_404(Conversation, pk=pk)
    if not conv.members.filter(user=request.user).exists():
        return JsonResponse({"error": "Not a member"}, status=403)

    gif_url = request.POST.get("gif_url", "")
    gif_id  = request.POST.get("gif_id", "")
    if not gif_url:
        return JsonResponse({"error": "No GIF"}, status=400)

    msg = Message.objects.create(
        conversation=conv,
        sender=request.user,
        text="",
    )
    Attachment.objects.create(
        message=msg,
        file_type="gif",
        gif_url=gif_url,
        gif_id=gif_id,
    )
    conv.save(update_fields=["updated_at"])
    return JsonResponse({"ok": True})