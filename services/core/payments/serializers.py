from rest_framework import serializers


class CreateOrderSerializer(serializers.Serializer):
    """Serializer for the request to create a payment order."""

    amount = serializers.IntegerField(min_value=1, help_text="Amount in INR (e.g. 49, 99, 199).")


class OrderResponseSerializer(serializers.Serializer):
    """Serializer for the response after successfully creating a payment order."""

    order_id = serializers.CharField(help_text="The unique Razorpay order ID.")
    amount = serializers.IntegerField(help_text="The total amount in Paise.")
    key = serializers.CharField(help_text="The public Razorpay Key ID.")
    xp_amount = serializers.IntegerField(help_text="The amount of XP that will be awarded.")


class VerifyPaymentSerializer(serializers.Serializer):
    """Serializer for the request to verify a payment."""

    razorpay_order_id = serializers.CharField(help_text="The order ID returned by Razorpay when the order was created.")
    razorpay_payment_id = serializers.CharField(help_text="The payment ID returned by Razorpay after a successful payment.")
    razorpay_signature = serializers.CharField(help_text="The signature returned by Razorpay to verify the payment authenticity.")


class VerifyPaymentResponseSerializer(serializers.Serializer):
    """Serializer for the response after verifying a payment."""

    status = serializers.CharField(help_text="The status of the verification (e.g., 'success').")
    new_xp = serializers.IntegerField(help_text="The user's updated total XP.")
