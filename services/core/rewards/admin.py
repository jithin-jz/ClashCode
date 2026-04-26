from django.contrib import admin

from .models import DailyCheckIn


@admin.register(DailyCheckIn)
class DailyCheckInAdmin(admin.ModelAdmin):
    list_display = ["user", "check_in_date", "streak_day", "xp_earned", "created_at"]
    list_filter = ["check_in_date", "streak_day"]
    search_fields = ["user__username"]
    readonly_fields = ["created_at"]
    ordering = ["-check_in_date"]
