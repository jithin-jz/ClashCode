import uuid

from django.contrib.auth.models import User
from django.db import models


class UserCertificate(models.Model):
    """
    Certificate issued when user completes the full global challenge track.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="certificate")
    certificate_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    issued_date = models.DateTimeField(auto_now_add=True)
    certificate_image = models.ImageField(upload_to="certificates/", null=True, blank=True)
    is_valid = models.BooleanField(default=True)
    completion_count = models.IntegerField(help_text="Number of challenges completed when certificate was issued")

    class Meta:
        ordering = ["-issued_date"]
        # Keep existing table name so migration is state-only and data is preserved.
        db_table = "challenges_usercertificate"

    def __str__(self):
        return f"Certificate for {self.user.username} - {self.certificate_id}"

    @property
    def verification_url(self):
        from django.conf import settings

        base_url = settings.FRONTEND_URL or "http://localhost:5173"
        return f"{base_url}/verify/{self.certificate_id}"


class CertificateVerificationLog(models.Model):
    """
    Logs every time a certificate is verified.
    Useful for analytics and detecting abuse.
    """

    certificate = models.ForeignKey(UserCertificate, on_delete=models.CASCADE, related_name="verification_logs")
    verified_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    referer = models.URLField(null=True, blank=True)

    class Meta:
        ordering = ["-verified_at"]

    def __str__(self):
        return f"Verification for {self.certificate.certificate_id} at {self.verified_at}"
