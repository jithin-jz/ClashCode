from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    # Columns visible in the payment list
    list_display = (
        "user",
        "razorpay_order_id",
        "razorpay_payment_id",
        "amount",
        "xp_amount",
        "status",
        "created_at",
    )

    # Quick filters on the right sidebar
    list_filter = (
        "status",
        "created_at",
    )

    # Search across common identifiers
    search_fields = (
        "user__username",
        "user__email",
        "razorpay_order_id",
        "razorpay_payment_id",
    )

    # Default ordering (latest payments first)
    ordering = ("-created_at",)

    # Prevent accidental edits to immutable fields
    readonly_fields = (
        "razorpay_order_id",
        "razorpay_payment_id",
        "created_at",
    )

    # Group fields logically in the detail view
    fieldsets = (
        (
            "User",
            {
                "fields": ("user",),
            },
        ),
        (
            "Payment Details",
            {
                "fields": (
                    "razorpay_order_id",
                    "razorpay_payment_id",
                    "amount",
                    "xp_amount",
                    "status",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at",),
            },
        ),
    )
