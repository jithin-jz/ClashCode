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
