from django.contrib.auth.models import User
from django.db import models


class Challenge(models.Model):
    """
    Represents a coding challenge/task.
    """

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(help_text="Markdown supported problem description")
    initial_code = models.TextField(help_text="Starter code for the user")
    test_code = models.TextField(help_text="Hidden python code to assert the user solution")
    order = models.IntegerField(default=0, help_text="Order in the campaign level map")

    # New Field: created_for_user
    # If null, it is a global level (e.g. Level 1)
    # If set, it is a personalized level for that user only
    created_for_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="personalized_challenges",
    )

    xp_reward = models.IntegerField(default=50)
    time_limit = models.IntegerField(default=300, help_text="Suggested time in seconds for bonus")

    # Star rating target time
    target_time_seconds = models.IntegerField(
        default=600,
        help_text="Target completion time for 3-star rating (10 minutes default)",
    )

    is_published = models.BooleanField(default=True, help_text="If false, only staff can see this challenge")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        user_str = f" [User: {self.created_for_user.username}]" if self.created_for_user else " [Global]"
        return f"{self.order}. {self.title}{user_str}"


class UserProgress(models.Model):
    """
    Tracks a user's progress on a challenge.
    """

    class Status(models.TextChoices):
        LOCKED = "LOCKED", "Locked"
        UNLOCKED = "UNLOCKED", "Unlocked"
        COMPLETED = "COMPLETED", "Completed"

    user = models.ForeignKey(User, related_name="challenge_progress", on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, related_name="user_progress", on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.LOCKED)
    stars = models.IntegerField(default=0, help_text="0-3 stars based on performance")
    ai_hints_purchased = models.IntegerField(default=0, help_text="Number of AI hints purchased for this level.")

    # Time tracking for star rating
    started_at = models.DateTimeField(null=True, blank=True, help_text="When user first accessed this challenge")

    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["user", "challenge"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "completed_at"]),
            models.Index(fields=["challenge", "status"]),
        ]

    def __str__(self):
        return f"Progress: {self.user.username} - {self.challenge.title} ({self.status})"
