from django.contrib.auth.models import User
from django.db import models


class DailyCheckIn(models.Model):
    """
    Model to track daily check-ins and reward streaks.

    This model enforces a unique check-in per day per user.
    It stores the calculated streak day (1-7) and the XP earned for that specific check-in.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="check_ins")
    check_in_date = models.DateField(auto_now_add=True)
    streak_day = models.IntegerField(default=1)  # 1-7 for the streak day
    xp_earned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-check_in_date"]
        unique_together = ["user", "check_in_date"]
        indexes = [
            models.Index(fields=["user", "-check_in_date"]),
        ]
        verbose_name = "Daily Check-In"
        verbose_name_plural = "Daily Check-Ins"

    def __str__(self):
        return f"{self.user.username} - Day {self.streak_day} - {self.check_in_date}"
