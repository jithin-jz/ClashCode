from django.contrib import admin

from .models import Purchase, StoreItem


@admin.register(StoreItem)
class StoreItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "cost", "is_active", "created_at")
    list_filter = ("category", "is_active")
    search_fields = ("name", "description")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "item", "purchased_at")
    list_filter = ("purchased_at",)
    search_fields = ("user__username", "item__name")
