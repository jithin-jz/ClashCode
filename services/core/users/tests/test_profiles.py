from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import UserFollow


class ProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="me", password="password")
        self.other = User.objects.create_user(username="other", password="password")
        self.client.force_authenticate(user=self.user)

    def test_get_own_profile(self):
        url = reverse("get_current_user")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "me")

    def test_update_profile(self):
        url = reverse("update_profile")
        data = {"bio": "New Bio"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["profile"]["bio"], "New Bio")

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, "New Bio")

    def test_follow_user(self):
        url = reverse("toggle_follow", kwargs={"username": "other"})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_following"])

        self.assertTrue(UserFollow.objects.filter(follower=self.user, following=self.other).exists())

        # Test unfollow
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_following"])
        self.assertFalse(UserFollow.objects.filter(follower=self.user, following=self.other).exists())

    def test_get_public_profile(self):
        url = reverse("profile_detail", kwargs={"username": "other"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "other")
        self.assertIn("is_following", response.data)

    def test_suggested_users(self):
        url = reverse("suggested_users")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see 'other' in suggestions
        usernames = [u["username"] for u in response.data]
        self.assertIn("other", usernames)
