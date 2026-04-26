import os

from challenges.models import Challenge
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class LearningViewTests(APITestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username="staff", password="password", is_staff=True)
        self.regular_user = User.objects.create_user(username="player", password="password")
        self.challenge = Challenge.objects.create(
            title="L1",
            slug="l1",
            order=1,
            description="D",
            initial_code="i",
            test_code="t",
        )
        os.environ["INTERNAL_API_KEY"] = "secret-key"

    def test_internal_list_requires_key(self):
        url = reverse("challenge-internal-list")

        # No key
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Wrong key
        response = self.client.get(url, HTTP_X_INTERNAL_API_KEY="wrong")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Correct key
        response = self.client.get(url, HTTP_X_INTERNAL_API_KEY="secret-key")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_internal_context_requires_key(self):
        url = reverse("challenge-internal-context", kwargs={"slug": "l1"})

        # Correct key
        response = self.client.get(url, HTTP_X_INTERNAL_API_KEY="secret-key")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["challenge_title"], "L1")

    def test_staff_create_challenge(self):
        self.client.force_authenticate(user=self.staff_user)
        url = reverse("challenge-list")
        data = {
            "title": "New",
            "slug": "new",
            "order": 10,
            "description": "D",
            "initial_code": "i",
            "test_code": "t",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_regular_user_cannot_create_challenge(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("challenge-list")
        data = {"title": "New"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
