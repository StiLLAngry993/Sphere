from django.db import models
from django.conf import settings


# ──────────────────────────────────────────────────────────
# CONVERSATION
# Covers both DMs (is_group=False) and group chats
# ──────────────────────────────────────────────────────────
class Conversation(models.Model):
    is_group    = models.BooleanField(default=False)
    group_name  = models.CharField(max_length=100, blank=True)
    group_image = models.ImageField(
        upload_to="chats/group_images/",
        blank=True,
        null=True
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        if self.is_group:
            return f"Group: {self.group_name}"
        members = self.members.all()[:2]
        return "DM: " + " & ".join(m.user.username for m in members)

    def get_other_member(self, current_user):
        """For DMs — returns the other participant."""
        return self.members.exclude(user=current_user).select_related("user").first()

    def last_message(self):
        return self.messages.filter(deleted=False).order_by("-created_at").first()

    def unread_count(self, user):
        """Messages not yet read by this user."""
        read_ids = ReadReceipt.objects.filter(
            user=user,
            message__conversation=self
        ).values_list("message_id", flat=True)
        return self.messages.filter(
            deleted=False
        ).exclude(
            sender=user
        ).exclude(
            id__in=read_ids
        ).count()


# ──────────────────────────────────────────────────────────
# CONVERSATION MEMBER
# Tracks who is in which conversation + their role
# ──────────────────────────────────────────────────────────
class ConversationMember(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="members"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations"
    )
    joined_at  = models.DateTimeField(auto_now_add=True)
    is_admin   = models.BooleanField(default=False)
    is_muted   = models.BooleanField(default=False)
    nickname   = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ("conversation", "user")
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user.username} in {self.conversation_id}"

    def display_name(self):
        return self.nickname or self.user.display_name or self.user.username


# ──────────────────────────────────────────────────────────
# MESSAGE
# Supports text, replies, edits, soft-delete
# ──────────────────────────────────────────────────────────
class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_messages"
    )
    text       = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited     = models.BooleanField(default=False)
    edited_at  = models.DateTimeField(null=True, blank=True)

    # Reply threading
    reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies"
    )

    # Soft delete — message stays in DB but is hidden
    deleted    = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        preview = self.text[:40] if self.text else "[attachment]"
        return f"{self.sender.username if self.sender else 'deleted'}: {preview}"

    def is_visible(self):
        return not self.deleted


# ──────────────────────────────────────────────────────────
# ATTACHMENT
# Separate from message so one message can have many files
# ──────────────────────────────────────────────────────────
class Attachment(models.Model):
    TYPE_CHOICES = [
        ("image",  "Image"),
        ("video",  "Video"),
        ("audio",  "Audio"),
        ("file",   "File"),
        ("gif",    "GIF"),
        ("voice",  "Voice Message"),
    ]

    message    = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="attachments"
    )
    file_type  = models.CharField(max_length=10, choices=TYPE_CHOICES)
    file       = models.FileField(
        upload_to="chats/attachments/",
        blank=True,
        null=True
    )
    # For GIFs from Giphy — no file upload needed, just a URL
    gif_url    = models.URLField(blank=True)
    gif_id     = models.CharField(max_length=100, blank=True)

    # File metadata
    file_name  = models.CharField(max_length=255, blank=True)
    file_size  = models.PositiveBigIntegerField(default=0)     # bytes
    duration   = models.FloatField(default=0)                  # seconds (audio/video)
    width      = models.IntegerField(default=0)                # px (image/video)
    height     = models.IntegerField(default=0)                # px (image/video)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_type} in msg {self.message_id}"

    @property
    def url(self):
        if self.gif_url:
            return self.gif_url
        return self.file.url if self.file else ""

    @property
    def is_gif(self):
        return self.file_type == "gif"


# ──────────────────────────────────────────────────────────
# MESSAGE REACTION
# ──────────────────────────────────────────────────────────
class MessageReaction(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="reactions"
    )
    user  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_reactions"
    )
    emoji = models.CharField(max_length=10)  
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # One reaction per emoji per user per message
        unique_together = ("message", "user", "emoji")

    def __str__(self):
        return f"{self.user.username} {self.emoji} → msg {self.message_id}"


# ──────────────────────────────────────────────────────────
# READ RECEIPT
# Tracks exactly when each user read each message
# Enables Seen
# ──────────────────────────────────────────────────────────
class ReadReceipt(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="read_receipts"
    )
    user    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="read_receipts"
    )
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("message", "user")

    def __str__(self):
        return f"{self.user.username} read msg {self.message_id} at {self.read_at}"