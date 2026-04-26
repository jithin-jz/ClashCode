from django.contrib import admin

from .models import Challenge, UserProgress


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "xp_reward", "slug", "target_time_seconds")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "description")


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "challenge", "status", "stars", "completed_at")
    list_filter = ("status", "stars")
    search_fields = ("user__username", "challenge__title")
