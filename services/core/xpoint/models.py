from django.contrib.auth.models import User
from django.db import models


class XPTransaction(models.Model):
    """
    Audit log for all XP changes in the system.
    Ensures every point earned or spent is traceable.
    """

    SOURCE_CHOICES = [
        ("check_in", "Daily Check-in"),
        ("purchase", "Store Purchase"),
        ("referral", "Referral Reward"),
        ("challenge", "Challenge Completion"),
        ("admin", "Admin Adjustment"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="xp_transactions")
    amount = models.IntegerField(help_text="Amount of XP (positive for gain, negative for spend)")
    balance_after = models.IntegerField(help_text="XP balance after this transaction")
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["source"]),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.amount} XP from {self.source}"
