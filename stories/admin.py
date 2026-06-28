from django.contrib import admin
from .models import Story

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display  = ("author", "media_type", "created_at", "expires_at", "view_count")
    list_filter   = ("media_type",)
    search_fields = ("author__username",)
    readonly_fields = ("created_at", "expires_at", "viewers")