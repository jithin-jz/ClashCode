from django.contrib.auth.models import User
from django.urls import reverse
from notifications.models import FCMToken, Notification
from rest_framework import status
from rest_framework.test import APITestCase


class NotificationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="notify_user", password="password")
        self.other_user = User.objects.create_user(username="actor_user", password="password")
        self.client.force_authenticate(user=self.user)

        # Create some notifications
        self.n1 = Notification.objects.create(recipient=self.user, actor=self.other_user, verb="followed you")
        self.n2 = Notification.objects.create(recipient=self.user, actor=self.other_user, verb="liked your post")

    def test_list_notifications(self):
        url = reverse("notification-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["unread_count"], 2)
        # Should return 2 notifications
        self.assertEqual(len(response.data["results"]), 2)
        # Verify both notification IDs are present
        returned_ids = [n["id"] for n in response.data["results"]]
        self.assertIn(self.n1.id, returned_ids)
        self.assertIn(self.n2.id, returned_ids)

    def test_mark_as_read(self):
        url = reverse("notification-mark-read", kwargs={"pk": self.n1.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.n1.refresh_from_db()
        self.assertTrue(self.n1.is_read)

    def test_mark_all_as_read(self):
        url = reverse("notification-mark-all-read")
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Notification.objects.filter(recipient=self.user, is_read=False).count(), 0)

    def test_clear_all_notifications(self):
        url = reverse("notification-clear-all")
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Notification.objects.filter(recipient=self.user).count(), 0)

    def test_fcm_token_registration(self):
        url = reverse("fcm-token-list")
        data = {"token": "fake-fcm-token-123", "device_id": "phone-abc"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FCMToken.objects.filter(user=self.user).count(), 1)

        # Test update (same token, different device_id or re-registration)
        data["device_id"] = "phone-xyz"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(FCMToken.objects.get(token="fake-fcm-token-123").device_id, "phone-xyz")

    def test_notification_isolation(self):
        # Create notification for another user
        stranger = User.objects.create_user(username="stranger", password="password")
        Notification.objects.create(recipient=stranger, actor=self.other_user, verb="messaged you")

        url = reverse("notification-list")
        response = self.client.get(url)
        # Should still only see 2 notifications (isolation check)
        self.assertEqual(len(response.data["results"]), 2)
