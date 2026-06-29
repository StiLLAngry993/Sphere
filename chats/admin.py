from django.contrib import admin
from .models import (
    Conversation, ConversationMember,
    Message, Attachment, MessageReaction, ReadReceipt
)


class MemberInline(admin.TabularInline):
    model  = ConversationMember
    extra  = 0
    fields = ("user", "is_admin", "is_muted", "nickname", "joined_at")
    readonly_fields = ("joined_at",)


class AttachmentInline(admin.TabularInline):
    model  = Attachment
    extra  = 0
    fields = ("file_type", "file", "gif_url", "file_name", "file_size")


class ReactionInline(admin.TabularInline):
    model  = MessageReaction
    extra  = 0
    fields = ("user", "emoji", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display   = ("id", "__str__", "is_group", "created_at", "updated_at")
    list_filter    = ("is_group",)
    search_fields  = ("group_name", "members__user__username")
    inlines        = [MemberInline]
    readonly_fields = ("created_at", "updated_at")


@admin.register(ConversationMember)
class ConversationMemberAdmin(admin.ModelAdmin):
    list_display  = ("user", "conversation", "is_admin", "is_muted", "joined_at")
    list_filter   = ("is_admin", "is_muted")
    search_fields = ("user__username", "conversation__group_name")
    readonly_fields = ("joined_at",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display   = ("id", "sender", "conversation", "short_text", "created_at", "edited", "deleted")
    list_filter    = ("deleted", "edited")
    search_fields  = ("sender__username", "text")
    readonly_fields = ("created_at", "edited_at", "deleted_at")
    inlines        = [AttachmentInline, ReactionInline]

    @admin.display(description="Text")
    def short_text(self, obj):
        return obj.text[:60] if obj.text else "[attachment]"


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display  = ("id", "message", "file_type", "file_name", "file_size", "uploaded_at")
    list_filter   = ("file_type",)
    search_fields = ("file_name", "message__sender__username")
    readonly_fields = ("uploaded_at",)


@admin.register(MessageReaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display  = ("user", "emoji", "message", "created_at")
    search_fields = ("user__username", "emoji")
    readonly_fields = ("created_at",)


@admin.register(ReadReceipt)
class ReadReceiptAdmin(admin.ModelAdmin):
    list_display  = ("user", "message", "read_at")
    search_fields = ("user__username",)
    readonly_fields = ("read_at",)