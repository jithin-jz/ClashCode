from django.contrib.auth.models import User
from django.db import models


class AdminAuditLog(models.Model):
    admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_actions",
    )
    admin_username = models.CharField(max_length=150, db_index=True)
    action = models.CharField(max_length=255, db_index=True)
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="target_of_admin_actions",
    )
    target_username = models.CharField(max_length=150, blank=True, default="", db_index=True)
    target_email = models.EmailField(blank=True, default="")
    details = models.JSONField(default=dict, blank=True)
    actor_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True, default="")
    request_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        admin_name = self.admin_username or (self.admin.username if self.admin else "unknown")
        return f"{admin_name} - {self.action} - {self.timestamp}"


class AdminNote(models.Model):
    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="admin_notes_authored",
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="admin_notes",
    )
    body = models.TextField(max_length=2000)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return f"Note by {self.admin.username} for {self.target_user.username}"


class AdminReport(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_REVIEW = "IN_REVIEW", "In Review"
        RESOLVED = "RESOLVED", "Resolved"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="admin_reports",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_reports_created",
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_reports_resolved",
    )
    title = models.CharField(max_length=200)
    summary = models.TextField(max_length=2000)
    category = models.CharField(max_length=50, default="GENERAL", db_index=True)
    priority = models.CharField(
        max_length=16,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )
    context = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["status", "-created_at"]

    def __str__(self):
        return f"{self.title} ({self.target_user.username})"
