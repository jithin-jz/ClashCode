from django.contrib import admin

from .models import Achievement, UserAchievement, UserAchievementProgress


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "slug",
        "category",
        "xp_reward",
        "target_value",
        "is_secret",
        "order",
    ]
    list_filter = ["category", "is_secret"]
    search_fields = ["title", "description", "slug"]
    prepopulated_fields = {"slug": ("title",)}
    ordering = ["order", "title"]


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ["user", "achievement", "unlocked_at"]
    list_filter = ["unlocked_at", "achievement__category"]
    search_fields = ["user__username", "achievement__title"]
    raw_id_fields = ["user", "achievement"]


@admin.register(UserAchievementProgress)
class UserAchievementProgressAdmin(admin.ModelAdmin):
    list_display = ["user", "achievement", "current_value", "updated_at"]
    list_filter = ["updated_at", "achievement__category"]
    search_fields = ["user__username", "achievement__title"]
    raw_id_fields = ["user", "achievement"]
