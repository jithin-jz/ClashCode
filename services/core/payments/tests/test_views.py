from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from payments.models import Payment


class PaymentViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", password="password")
        self.other_user = User.objects.create_user(
            username="other", password="password"
        )
        self.verify_url = reverse("verify-payment")
        self.create_order_url = reverse("create-order")

    @patch("payments.services.PaymentService.get_razorpay_client")
    def test_create_order_success(self, mock_get_client):
        # Mocking the Razorpay client and order creation
        mock_client = MagicMock()
        mock_client.order.create.return_value = {"id": "order_mock_123"}
        mock_get_client.return_value = mock_client

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.create_order_url, {"amount": 99}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["order_id"], "order_mock_123")
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(Payment.objects.first().xp_amount, 100)

    @patch("payments.services.PaymentService.get_razorpay_client")
    def test_create_order_invalid_amount(self, mock_get_client):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.create_order_url, {"amount": 50}, format="json"
        )  # Not in map
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("payments.services.PaymentService.get_razorpay_client")
    @patch("payments.services.XPService.add_xp")
    def test_verify_payment_success(self, mock_add_xp, mock_get_client):
        # Setup mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_add_xp.return_value = 200

        payment = Payment.objects.create(
            user=self.user,
            razorpay_order_id="order_test_verified",
            amount=99,
            xp_amount=100,
            status="pending",
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.verify_url,
            {
                "razorpay_order_id": payment.razorpay_order_id,
                "razorpay_payment_id": "pay_xyz",
                "razorpay_signature": "sig_xyz",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "success")
        mock_add_xp.assert_called_once()

    @patch("payments.services.PaymentService.get_razorpay_client")
    @patch("payments.services.XPService.add_xp")
    def test_rejects_verification_for_other_users_order(
        self, mock_add_xp, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        payment = Payment.objects.create(
            user=self.other_user,
            razorpay_order_id="order_test_1",
            amount=99,
            xp_amount=100,
            status="pending",
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.verify_url,
            {
                "razorpay_order_id": payment.razorpay_order_id,
                "razorpay_payment_id": "pay_test_1",
                "razorpay_signature": "sig_test_1",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "pending")
        mock_add_xp.assert_not_called()

    @patch("payments.services.PaymentService.get_razorpay_client")
    @patch("payments.services.XPService.add_xp", return_value=200)
    def test_idempotent_success_does_not_recredit_xp(
        self, mock_add_xp, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        payment = Payment.objects.create(
            user=self.user,
            razorpay_order_id="order_test_2",
            amount=99,
            xp_amount=100,
            status="pending",
        )
        self.client.force_authenticate(user=self.user)

        payload = {
            "razorpay_order_id": payment.razorpay_order_id,
            "razorpay_payment_id": "pay_test_2",
            "razorpay_signature": "sig_test_2",
        }
        first = self.client.post(self.verify_url, payload, format="json")
        second = self.client.post(self.verify_url, payload, format="json")

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_add_xp.call_count, 1)
