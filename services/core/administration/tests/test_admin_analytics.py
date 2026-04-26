from challenges.models import Challenge, UserProgress
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from notifications.models import Notification
from rest_framework import status
from rest_framework.test import APIClient
from store.models import StoreItem

from administration.models import AdminAuditLog


class AdminAnalyticsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.super_admin = User.objects.create_user(
            username="superadmin",
            email="super@example.com",
            password="pass1234",
            is_staff=True,
            is_superuser=True,
        )
        # Create a regular user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass1234",
            last_login=timezone.now(),
        )
        # Update the profile created by signal
        self.profile = self.user.profile
        self.profile.provider = "github"
        self.profile.xp = 500
        self.profile.save()

        # Create a challenge and some progress
        self.challenge = Challenge.objects.create(title="Test Challenge", slug="test-challenge", xp_reward=100)
        UserProgress.objects.create(
            user=self.user,
            challenge=self.challenge,
            status=UserProgress.Status.COMPLETED,
            stars=3,
        )

        # Create a store item
        self.item = StoreItem.objects.create(name="Test Item", category="gems", cost=200)

    def test_admin_stats_view(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse("admin_stats")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_users"], 2)
        self.assertEqual(response.data["oauth_logins"], 1)
        self.assertEqual(response.data["total_gems"], 500)
        self.assertEqual(response.data["active_sessions"], 1)

    def test_challenge_analytics_view(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse("admin_challenge_analytics")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Test Challenge")
        self.assertEqual(response.data[0]["completions"], 1)
        self.assertEqual(response.data[0]["completion_rate"], 100.0)
        self.assertEqual(response.data[0]["avg_stars"], 3.0)

    def test_global_notification_broadcast(self):
        self.client.force_authenticate(user=self.super_admin)
        User.objects.create_user(username="recipient", email="rec@ex.com")

        url = reverse("admin_broadcast")
        data = {"message": "Hello everyone!", "reason": "Test broadcast"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("sent to 2 users", response.data["message"])

        # Check if notifications were created
        self.assertEqual(Notification.objects.count(), 2)

        # Check audit log
        audit = AdminAuditLog.objects.filter(action="SEND_GLOBAL_NOTIFICATION").latest("timestamp")
        self.assertEqual(audit.details["message"], "Hello everyone!")

    def test_system_integrity_view(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse("admin_system_integrity")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["users"], 2)
        self.assertEqual(response.data["challenges"], 1)
        self.assertEqual(response.data["store_items"], 1)
