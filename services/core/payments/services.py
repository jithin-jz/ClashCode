import logging

from django.conf import settings
from django.db import transaction
from xpoint.services import XPService

from .models import Payment

logger = logging.getLogger(__name__)

try:
    import razorpay
except Exception:
    razorpay = None


class PaymentService:
    """
    Business logic for handling payments and Razorpay interactions.
    """

    XP_PACKAGES = {
        49: 50,
        99: 100,
        199: 200,
        249: 250,
        499: 500,
        749: 800,
        999: 1000,
        1999: 2500,
    }

    @staticmethod
    def get_razorpay_client():
        """Initializes and returns the Razorpay client."""
        if razorpay is None:
            raise RuntimeError("Razorpay SDK is not available")
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            raise RuntimeError("Razorpay keys are not configured on the server")
        return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    @classmethod
    def create_order(cls, user, amount_inr):
        """Creates a Razorpay order and a pending Payment record."""
        if amount_inr not in cls.XP_PACKAGES:
            raise ValueError("Invalid package amount")

        client = cls.get_razorpay_client()
        xp_to_credit = cls.XP_PACKAGES[amount_inr]

        order_data = {
            "amount": int(amount_inr * 100),  # Amount in Paise
            "currency": "INR",
            "receipt": f"coc_{user.id}_{amount_inr}",
            "notes": {"user_id": str(user.id)},
        }

        order = client.order.create(data=order_data)

        Payment.objects.create(
            user=user,
            razorpay_order_id=order["id"],
            amount=amount_inr,
            xp_amount=xp_to_credit,
            status="pending",
        )

        return {
            "order_id": order["id"],
            "amount": order_data["amount"],
            "key": settings.RAZORPAY_KEY_ID,
            "xp_amount": xp_to_credit,
        }

    @classmethod
    def verify_payment(cls, user, order_id, payment_id, signature):
        """Verifies the Razorpay payment signature and credits XP."""
        client = cls.get_razorpay_client()

        # Verify signature
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }
        )

        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(razorpay_order_id=order_id)

            if payment.user_id != user.id:
                raise PermissionError("Order does not belong to authenticated user")

            if payment.status == "success":
                return {"status": "already_processed", "new_xp": user.profile.xp}

            payment.razorpay_payment_id = payment_id
            payment.status = "success"
            payment.save()

            new_xp = XPService.add_xp(
                user=user,
                amount=payment.xp_amount,
                source=XPService.SOURCE_PURCHASE,
            )

            return {"status": "success", "new_xp": new_xp}
