from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock


class AuthViewTests(APITestCase):
    @patch("auth.services.AuthService.request_otp")
    def test_request_otp_endpoint(self, mock_request_otp):
        url = reverse("otp_request")  # Ensure this matches your urls.py name
        data = {"email": "user@example.com"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "OTP sent successfully")
        mock_request_otp.assert_called_with("user@example.com")

    @patch("auth.services.AuthService.verify_otp")
    def test_verify_otp_endpoint_success(self, mock_verify):
        # Create a real user to avoid serialization issues with MagicMock
        user = User.objects.create_user(username="testuser", email="user@example.com")

        # Setup mock return value
        mock_verify.return_value = (
            user,
            {"access_token": "fake_access", "refresh_token": "fake_refresh"},
        )

        url = reverse("otp_verify")
        data = {"email": "user@example.com", "otp": "123456"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if JWT was set in the cookie
        self.assertIn("access_token", response.cookies)
        self.assertTrue(response.cookies["access_token"]["httponly"])

    def test_logout_endpoint(self):
        user = User.objects.create_user(username="logoutuser", password="pass")
        self.client.force_authenticate(user=user)

        url = reverse("logout")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify cookies are marked for deletion (max_age=0 or empty)
        self.assertEqual(response.cookies["access_token"].value, "")
