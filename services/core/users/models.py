from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extended user profile model that serves as the core identity record..

    Responsibilities:
    1.  **OAuth Integration**: Stores provider name and unique ID to link external accounts.
    2.  **Profile Data**: Stores public facing data like avatar, banner, and bio.
    3.  **Social/Gamification**: Tracks XP (experience points), referral system codes, and links.
    4.  **Security**: Temporarily stores OAuth tokens (access/refresh) for API usage.

    Relationships:
    - OneToOne with Django's built-in User model.
    - Self-referencing ForeignKey for the referral system (`referred_by`).
    """

    # Supported OAuth providers
    # 'local' is used for admin/superuser accounts created via CLI
    PROVIDER_CHOICES = [
        ("github", "GitHub"),
        ("google", "Google"),
        ("email", "Email OTP"),
        ("local", "Local/Admin"),
    ]

    # One-to-one link insures strict 1:1 relationship between auth user and profile
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        help_text="The associated Django User account.",
    )

    # Authentication Source
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        help_text="The OAuth provider used to create this account.",
    )
    provider_id = models.CharField(
        max_length=255,
        help_text="Unique ID returned by the OAuth provider (e.g., GitHub user ID).",
    )

    # Public Profile Visuals
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True, help_text="User's profile picture.")
    banner = models.ImageField(
        upload_to="banners/",
        blank=True,
        null=True,
        help_text="Profile background banner.",
    )
    bio = models.TextField(max_length=500, blank=True, null=True, help_text="Short user biography.")

    # OAuth Tokens (Sensitive)
    # Stored to allow backend to make API calls on behalf of the user (e.g. fetch repos)
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)

    # Linked Platforms (For display/social features, not auth)

    # Customization
    active_theme = models.CharField(max_length=50, default="vs-dark", help_text="Active Monaco Editor theme.")
    active_font = models.CharField(max_length=50, default="Fira Code", help_text="Active Editor Font Family.")
    active_effect = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Active Cursor Effect (e.g., 'fire', 'particles').",
    )
    active_victory = models.CharField(max_length=50, default="default", help_text="Active Victory Animation.")

    # Gamification & Referrals
    xp = models.IntegerField(default=0, help_text="Total Experience Points earned.")
    streak_freezes = models.IntegerField(default=0, help_text="Number of streak freezes available.")
    reward_cycle_start_date = models.DateField(
        null=True, blank=True, help_text="Start date of the current 7-day reward cycle."
    )
    referral_code = models.CharField(
        max_length=12,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique code for inviting others.",
    )

    # Who invited this user?
    referred_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referrals",
        help_text="The user who referred this account.",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Prevent same OAuth account from being reused
        unique_together = ["provider", "provider_id"]
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        indexes = [
            models.Index(fields=["-xp"]),
            models.Index(fields=["provider"]),
        ]

    def save(self, *args, **kwargs):
        # Auto-generate unique referral code if missing
        if not self.referral_code:
            import random
            import string

            while True:
                code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not UserProfile.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)

    def toggle_block(self):
        """Toggle the active status of the associated user."""
        # Soft block by disabling login access
        self.user.is_active = not self.user.is_active
        self.user.save()
        return self.user.is_active

    def __str__(self):
        # Human-readable identifier for admin/debugging
        return f"{self.user.username} ({self.provider})"


class UserFollow(models.Model):
    """Model to store follower/following relationships."""

    # User who initiates the follow
    follower = models.ForeignKey(User, related_name="following", on_delete=models.CASCADE)

    # User being followed
    following = models.ForeignKey(User, related_name="followers", on_delete=models.CASCADE)

    # Timestamp of follow action
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent duplicate follow relationships
        unique_together = ["follower", "following"]

        # Optimize follower/following queries
        indexes = [
            models.Index(fields=["follower", "following"]),
            models.Index(fields=["following", "follower"]),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    _ = sender, kwargs
    # Automatically create profile when a user is created
    if created and not hasattr(instance, "profile"):
        UserProfile.objects.create(
            user=instance,
            provider="local",
            provider_id=f"local_{instance.id}",
            bio="",
        )


@receiver(post_save, sender=UserProfile)
def trigger_leaderboard_update_on_profile(sender, instance, **kwargs):
    """
    Trigger real-time leaderboard update when a user profile is updated (XP, avatar, etc).
    """
    # Import inside to avoid circular dependencies
    from learning.tasks import update_leaderboard_cache

    update_leaderboard_cache.delay()
