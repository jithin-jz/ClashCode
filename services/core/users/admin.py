from django.contrib import admin

from .models import UserFollow, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    # Columns shown in the list view
    list_display = (
        "user",
        "provider",
        "provider_id",
        "xp",
        "referral_code",
        "referred_by",
        "created_at",
    )

    # Filters in the right sidebar
    list_filter = (
        "provider",
        "created_at",
    )

    # Fields searchable from the admin search bar
    search_fields = (
        "user__username",
        "user__email",
        "provider_id",
        "referral_code",
        "github_username",
        "leetcode_username",
    )

    # Default ordering
    ordering = ("-created_at",)

    # Fields that should not be editable manually
    readonly_fields = (
        "created_at",
        "updated_at",
        "referral_code",
    )

    # Group fields logically in the detail view
    fieldsets = (
        (
            "User",
            {
                "fields": ("user", "provider", "provider_id"),
            },
        ),
        (
            "Profile",
            {
                "fields": ("avatar_url", "banner_url", "bio"),
            },
        ),
        (
            "OAuth Tokens (Sensitive)",
            {
                "fields": ("access_token", "refresh_token"),
                "classes": ("collapse",),
            },
        ),
        (
            "Social & Gamification",
            {
                "fields": ("xp", "streak_freezes", "referral_code", "referred_by"),
            },
        ),
        (
            "Linked Platforms",
            {
                "fields": ("github_username", "leetcode_username"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = (
        "follower",
        "following",
        "created_at",
    )

    search_fields = (
        "follower__username",
        "following__username",
    )

    list_filter = ("created_at",)

    ordering = ("-created_at",)
