from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from challenges.models import Challenge, UserProgress
from certificates.models import UserCertificate
from certificates.services import CertificateService


class CertificateServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass"
        )

    def test_get_required_challenges(self):
        # Create 3 challenges
        for i in range(1, 4):
            Challenge.objects.create(order=i, title=f"C{i}", slug=f"c{i}", xp_reward=10)
        self.assertEqual(CertificateService.get_required_challenges(), 3)

    def test_get_completed_count(self):
        # Create 3 required challenges
        for i in range(1, 4):
            Challenge.objects.create(order=i, title=f"C{i}", slug=f"c{i}", xp_reward=10)

        # User completes 2 of them
        for i in range(1, 3):
            challenge = Challenge.objects.get(order=i)
            UserProgress.objects.create(
                user=self.user,
                challenge=challenge,
                status=UserProgress.Status.COMPLETED,
            )

        self.assertEqual(CertificateService.get_completed_count(self.user), 2)

        # User completes the 3rd one
        challenge = Challenge.objects.get(order=3)
        UserProgress.objects.create(
            user=self.user, challenge=challenge, status=UserProgress.Status.COMPLETED
        )
        self.assertEqual(CertificateService.get_completed_count(self.user), 3)

    def test_is_eligible(self):
        # Create challenges
        for i in range(1, 4):
            Challenge.objects.create(order=i, title=f"C{i}", slug=f"c{i}", xp_reward=10)

        self.assertFalse(CertificateService.is_eligible(self.user))

        # Complete all 3
        for i in range(1, 4):
            challenge = Challenge.objects.get(order=i)
            UserProgress.objects.create(
                user=self.user,
                challenge=challenge,
                status=UserProgress.Status.COMPLETED,
            )

        self.assertTrue(CertificateService.is_eligible(self.user))

    def test_get_or_create_certificate(self):
        # Create and complete challenges
        for i in range(1, 4):
            challenge = Challenge.objects.create(
                order=i, title=f"C{i}", slug=f"c{i}", xp_reward=10
            )
            UserProgress.objects.create(
                user=self.user,
                challenge=challenge,
                status=UserProgress.Status.COMPLETED,
            )

        # Create certificate
        cert = CertificateService.get_or_create_certificate(self.user)
        self.assertIsNotNone(cert)
        self.assertEqual(cert.user, self.user)
        self.assertEqual(cert.completion_count, 3)

        # Try again - should return the same one
        cert2 = CertificateService.get_or_create_certificate(self.user)
        self.assertEqual(cert.id, cert2.id)

    def test_get_eligibility_status(self):
        # Create 3 challenges
        for i in range(1, 4):
            Challenge.objects.create(order=i, title=f"C{i}", slug=f"c{i}", xp_reward=10)

        status = CertificateService.get_eligibility_status(self.user)
        self.assertEqual(status["completed_challenges"], 0)
        self.assertEqual(status["required_challenges"], 3)
        self.assertEqual(status["remaining_challenges"], 3)
        self.assertFalse(status["eligible"])
        self.assertFalse(status["has_certificate"])
