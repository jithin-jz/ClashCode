from django.conf import settings
from django.db import models


class Payment(models.Model):
    """
    Model to track payment transactions for XP purchases.
    Stores Razorpay IDs and the status of the transaction.
    """

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    )
    # SET_NULL: financial records must survive account deletion (accounting/refunds).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Amount in INR
    xp_amount = models.IntegerField()  # Amount of XP to credit
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        username = self.user.username if self.user else "deleted-user"
        return f"{username} - {self.amount} - {self.status}"
