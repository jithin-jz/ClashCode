import hmac
import json
import logging
from hashlib import sha256

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

    @staticmethod
    def _mark_paid(payment, payment_id):
        """
        Marks a locked Payment as successful and credits its XP exactly once.
        Must be called inside transaction.atomic() with the row locked.
        Returns True when this call performed the credit.
        """
        if payment.status == "success":
            return False

        payment.razorpay_payment_id = payment_id
        payment.status = "success"
        payment.save(update_fields=["razorpay_payment_id", "status"])

        if payment.user is None:
            # Account was deleted after paying; keep the record, nothing to credit.
            logger.warning(f"Payment {payment.razorpay_order_id} captured for a deleted account")
            return True

        XPService.add_xp(
            user=payment.user,
            amount=payment.xp_amount,
            source=XPService.SOURCE_PURCHASE,
        )
        return True

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

            if not cls._mark_paid(payment, payment_id):
                user.profile.refresh_from_db()
                return {"status": "already_processed", "new_xp": user.profile.xp}

            user.profile.refresh_from_db()
            return {"status": "success", "new_xp": user.profile.xp}

    @staticmethod
    def verify_webhook_signature(body: bytes, signature: str) -> bool:
        """Razorpay signs the raw webhook body with HMAC-SHA256 using the webhook secret."""
        secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", "") or ""
        if not secret or not signature:
            return False
        expected = hmac.new(secret.encode("utf-8"), body, sha256).hexdigest()
        return hmac.compare_digest(expected, signature.strip())

    @classmethod
    def handle_webhook(cls, body: bytes, signature: str) -> str:
        """
        Server-to-server confirmation from Razorpay. Credits XP even when the
        browser never called verify-payment (closed tab, network drop).

        Returns a short outcome string; raises PermissionError on a bad signature.
        """
        if not cls.verify_webhook_signature(body, signature):
            raise PermissionError("Invalid webhook signature")

        event = json.loads(body.decode("utf-8"))
        event_type = event.get("event", "")
        entity = event.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = entity.get("order_id")
        payment_id = entity.get("id")

        if event_type not in {"payment.captured", "order.paid", "payment.failed"} or not order_id:
            return "ignored"

        with transaction.atomic():
            payment = Payment.objects.select_for_update().filter(razorpay_order_id=order_id).first()
            if payment is None:
                logger.warning(f"Razorpay webhook for unknown order {order_id}")
                return "unknown_order"

            if event_type == "payment.failed":
                if payment.status == "pending":
                    payment.status = "failed"
                    payment.razorpay_payment_id = payment_id
                    payment.save(update_fields=["status", "razorpay_payment_id"])
                return "failed"

            expected_paise = int(payment.amount * 100)
            if entity.get("amount") is not None and int(entity["amount"]) != expected_paise:
                logger.error(
                    f"Razorpay amount mismatch for {order_id}: got {entity.get('amount')}, expected {expected_paise}"
                )
                return "amount_mismatch"

            return "credited" if cls._mark_paid(payment, payment_id) else "already_processed"
