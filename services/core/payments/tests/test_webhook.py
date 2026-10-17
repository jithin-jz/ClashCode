import hmac
import json
from hashlib import sha256

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from payments.models import Payment

SECRET = "whsec_test"


def _signed(body: dict) -> tuple[bytes, str]:
    raw = json.dumps(body).encode()
    return raw, hmac.new(SECRET.encode(), raw, sha256).hexdigest()


def _event(event_type: str, order_id: str, amount: int = 9900, payment_id: str = "pay_1") -> dict:
    return {
        "event": event_type,
        "payload": {"payment": {"entity": {"id": payment_id, "order_id": order_id, "amount": amount}}},
    }


@override_settings(RAZORPAY_WEBHOOK_SECRET=SECRET)
class RazorpayWebhookTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", email="b@example.com", password="pw")
        self.payment = Payment.objects.create(
            user=self.user, razorpay_order_id="order_wh", amount=99, xp_amount=100, status="pending"
        )
        self.url = reverse("razorpay-webhook")

    def _post(self, body: dict, signature: str | None = None):
        raw, good_signature = _signed(body)
        return self.client.post(
            self.url,
            data=raw,
            content_type="application/json",
            HTTP_X_RAZORPAY_SIGNATURE=signature if signature is not None else good_signature,
        )

    def test_captured_payment_credits_xp_once(self):
        start = self.user.profile.xp
        first = self._post(_event("payment.captured", "order_wh"))
        second = self._post(_event("order.paid", "order_wh"))

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data["status"], "credited")
        self.assertEqual(second.data["status"], "already_processed")
        self.payment.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.payment.status, "success")
        self.assertEqual(self.user.profile.xp, start + 100)

    def test_invalid_signature_is_rejected(self):
        response = self._post(_event("payment.captured", "order_wh"), signature="bad")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "pending")

    @override_settings(RAZORPAY_WEBHOOK_SECRET="")
    def test_rejected_when_secret_not_configured(self):
        response = self._post(_event("payment.captured", "order_wh"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_amount_mismatch_does_not_credit(self):
        start = self.user.profile.xp
        response = self._post(_event("payment.captured", "order_wh", amount=100))
        self.assertEqual(response.data["status"], "amount_mismatch")
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.xp, start)

    def test_failed_payment_marks_failed(self):
        self._post(_event("payment.failed", "order_wh"))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "failed")

    def test_unknown_order_is_acknowledged(self):
        response = self._post(_event("payment.captured", "order_missing"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "unknown_order")

    def test_payment_record_survives_account_deletion(self):
        self.user.delete()
        self.payment.refresh_from_db()
        self.assertIsNone(self.payment.user)
        response = self._post(_event("payment.captured", "order_wh"))
        self.assertEqual(response.data["status"], "credited")
