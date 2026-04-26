from django.db import models

# UserProfile and UserFollow have been moved to the 'users' app.


class EmailOTP(models.Model):
    """
    Temporary storage for Email One-Time Passwords.

    OTPs are short-lived (valid for 10 minutes) and are deleted after successful verification.
    """

    email = models.EmailField()
    otp = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - OTP"


class SecurityAuditLog(models.Model):
    """
    Audit log for security-sensitive authentication events.
    Essential for production security monitoring and incident response.
    """

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_logs",
    )
    email = models.EmailField(blank=True, db_index=True)
    action = models.CharField(max_length=100, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.CharField(max_length=512, blank=True)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "action"]),
        ]

    def __str__(self):
        return f"{self.action} - {self.email or self.user.username} - {self.timestamp}"
