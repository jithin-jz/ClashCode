from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from certificates.models import UserCertificate


class CertificateViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="pass")
        self.client.force_authenticate(user=self.user)

    @patch("certificates.services.CertificateService.get_eligibility_status")
    def test_check_eligibility_endpoint(self, mock_status):
        mock_status.return_value = {
            "eligible": False,
            "completed_challenges": 10,
            "required_challenges": 60,
            "has_certificate": False,
            "remaining_challenges": 50,
        }
        url = reverse("certificate-check-eligibility")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["completed_challenges"], 10)

    @patch("certificates.services.CertificateService.is_eligible")
    @patch("certificates.services.CertificateService.get_or_create_certificate")
    def test_my_certificate_eligible_creates(self, mock_get_create, mock_eligible):
        mock_eligible.return_value = True
        mock_cert = UserCertificate.objects.create(user=self.user, completion_count=60)
        mock_get_create.return_value = mock_cert

        url = reverse("certificate-my-certificate")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["certificate_id"], str(mock_cert.certificate_id))

    def test_verify_certificate_endpoint(self):
        cert = UserCertificate.objects.create(user=self.user, completion_count=60)
        url = reverse("certificate-verify", kwargs={"certificate_id": str(cert.certificate_id)})

        # Verify without authentication (AllowAny)
        self.client.force_authenticate(user=None)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["valid"])
        self.assertEqual(response.data["certificate"]["username"], self.user.username)

    def test_verify_invalid_certificate(self):
        url = reverse(
            "certificate-verify",
            kwargs={"certificate_id": "00000000-0000-0000-0000-000000000000"},
        )
        self.client.force_authenticate(user=None)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data["valid"])

    @patch("certificates.services.CertificateService.is_eligible")
    @patch("certificates.services.CertificateService.get_eligibility_status")
    def test_my_certificate_not_eligible(self, mock_status, mock_eligible):
        mock_eligible.return_value = False
        mock_status.return_value = {
            "eligible": False,
            "completed_challenges": 5,
            "required_challenges": 60,
            "has_certificate": False,
            "remaining_challenges": 55,
        }

        url = reverse("certificate-my-certificate")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["eligible"])
        self.assertEqual(response.data["completed_challenges"], 5)
