from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Follow


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "display_name",
        "email",
        "is_staff",
        "date_joined",
        "followers_count",
        "following_count",
    )
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("username", "display_name", "email")
    ordering = ("-date_joined",)

    fieldsets = UserAdmin.fieldsets + (
        ("Profile", {
            "fields": ("display_name", "profile_picture", "bio"),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Profile", {
            "fields": ("display_name", "profile_picture", "bio"),
        }),
    )

    @admin.display(description="Followers")
    def followers_count(self, obj):
        return obj.followers_count

    @admin.display(description="Following")
    def following_count(self, obj):
        return obj.following_count


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display  = ("follower", "following", "created_at")
    list_filter   = ("created_at",)
    search_fields = ("follower__username", "following__username")
    ordering      = ("-created_at",)
    readonly_fields = ("created_at",)