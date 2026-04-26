from django.contrib.auth.models import User
from django.db import models


class StoreItem(models.Model):
    CATEGORY_CHOICES = [
        ("THEME", "Theme"),
        ("FONT", "Font"),
        ("EFFECT", "Effect"),
        ("VICTORY", "Victory"),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    cost = models.IntegerField(help_text="Cost in XP")
    icon_name = models.CharField(max_length=50, help_text="Lucide icon name or image path identifier")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="ITEM")
    image = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Path to image in public folder (e.g. /store/dracula.png)",
    )
    item_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON data for functional items (e.g., theme_key)",
    )
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.cost} XP)"


class Purchase(models.Model):
    user = models.ForeignKey(User, related_name="purchases", on_delete=models.CASCADE)
    item = models.ForeignKey(StoreItem, related_name="purchases", on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-purchased_at"]
        unique_together = ["user", "item"]  # Optional: if items are one-time buy
        indexes = [
            models.Index(fields=["user", "item"]),
            models.Index(fields=["user", "-purchased_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} bought {self.item.name}"
