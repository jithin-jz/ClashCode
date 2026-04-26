from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from challenges.models import Challenge, UserProgress


class ChallengeCoreTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="player", email="player@example.com", password="password")
        # Profile is created by signal
        self.profile = self.user.profile
        self.client.force_authenticate(user=self.user)

        # Create a few global challenges
        self.c1 = Challenge.objects.create(
            title="Level 1",
            slug="l1",
            order=1,
            xp_reward=100,
            target_time_seconds=60,
            description="D1",
            initial_code="pass",
            test_code="assert True",
        )
        self.c2 = Challenge.objects.create(
            title="Level 2",
            slug="l2",
            order=2,
            xp_reward=200,
            target_time_seconds=120,
            description="D2",
            initial_code="pass",
            test_code="assert True",
        )
        self.c3 = Challenge.objects.create(
            title="Level 3",
            slug="l3",
            order=3,
            xp_reward=300,
            target_time_seconds=180,
            description="D3",
            initial_code="pass",
            test_code="assert True",
        )

    def test_challenge_list_locking_logic(self):
        url = reverse("challenge-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Level 1 should be UNLOCKED (first level)
        # Level 2 should be LOCKED
        # Level 3 should be LOCKED
        items = response.data
        self.assertEqual(items[0]["slug"], "l1")
        self.assertEqual(items[0]["status"], UserProgress.Status.UNLOCKED)

        self.assertEqual(items[1]["slug"], "l2")
        self.assertEqual(items[1]["status"], UserProgress.Status.LOCKED)

    @patch("learning.views.PistonExecutionService.execute_code")
    def test_unlock_next_level_after_completion(self, mock_execute):
        mock_execute.return_value = {"run": {"code": 0, "stderr": "", "stdout": ""}}
        # Complete Level 1
        url = reverse("challenge-submit", kwargs={"slug": "l1"})
        response = self.client.post(url, {"code": "pass"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "completed")

        # Now list again
        list_url = reverse("challenge-list")
        response = self.client.get(list_url)
        items = response.data

        # L1 should be COMPLETED, L2 should be UNLOCKED
        self.assertEqual(items[0]["status"], UserProgress.Status.COMPLETED)
        self.assertEqual(items[1]["status"], UserProgress.Status.UNLOCKED)
        self.assertEqual(items[2]["status"], UserProgress.Status.LOCKED)

    @patch("learning.views.PistonExecutionService.execute_code")
    def test_submit_requires_code_and_validates_server_side(self, mock_execute):
        url = reverse("challenge-submit", kwargs={"slug": "l1"})
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(url, {"passed": "true"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(f"{url}?passed=true", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        mock_execute.return_value = {"run": {"code": 0, "stderr": "", "stdout": ""}}
        response = self.client.post(url, {"code": "pass"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_execute.return_value = {"run": {"code": 1, "stderr": "AssertionError", "stdout": ""}}
        response = self.client.post(url, {"code": "bad"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_rejects_legacy_passed_flag(self):
        url = reverse("challenge-submit", kwargs={"slug": "l1"})
        response = self.client.post(url, {"passed": "true"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(url, {"passed": "false"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(f"{url}?passed=true", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("learning.views.PistonExecutionService.execute_code")
    def test_xp_reward_only_on_first_completion(self, mock_execute):
        mock_execute.return_value = {"run": {"code": 0, "stderr": "", "stdout": ""}}
        initial_xp = self.profile.xp

        # First completion of L1
        url = reverse("challenge-submit", kwargs={"slug": "l1"})
        self.client.post(url, {"code": "pass"}, format="json")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.xp, initial_xp + 100)

        # Second completion of L1
        self.client.post(url, {"code": "pass"}, format="json")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.xp, initial_xp + 100)  # Still same XP

    @patch("learning.views.PistonExecutionService.execute_code")
    def test_star_rating_penalties(self, mock_execute):
        mock_execute.return_value = {"run": {"code": 0, "stderr": "", "stdout": ""}}
        # 1. Test 3 Stars (Clean & Fast)
        url = reverse("challenge-submit", kwargs={"slug": "l1"})
        # We need to set started_at to test time penalty
        # Retrieve triggers setting started_at
        self.client.get(reverse("challenge-detail", kwargs={"slug": "l1"}))

        response = self.client.post(url, {"code": "pass"}, format="json")
        self.assertEqual(response.data["stars"], 3)

        # 2. Test 2 Stars (Slow completion)
        # Reset progress for L2
        UserProgress.objects.create(
            user=self.user,
            challenge=self.c2,
            started_at=timezone.now() - timedelta(seconds=500),  # > 2*120
        )
        url = reverse("challenge-submit", kwargs={"slug": "l2"})
        response = self.client.post(url, {"code": "pass"}, format="json")
        self.assertEqual(response.data["stars"], 2)  # Penalized for time

    @patch("learning.views.PistonExecutionService.execute_code")
    def test_ai_hint_purchase_penalty(self, mock_execute):
        mock_execute.return_value = {"run": {"code": 0, "stderr": "", "stdout": ""}}
        # Give user some XP to purchase hints
        self.profile.xp = 100
        self.profile.save()

        # Purchase 1 hint for L3
        url_purchase = reverse("challenge-purchase-ai-assist", kwargs={"slug": "l3"})
        self.client.post(url_purchase)

        # Complete L3
        url_submit = reverse("challenge-submit", kwargs={"slug": "l3"})
        # Retrieve to set started_at
        self.client.get(reverse("challenge-detail", kwargs={"slug": "l3"}))

        response = self.client.post(url_submit, {"code": "pass"}, format="json")
        # 3 stars - 1 hint = 2 stars
        self.assertEqual(response.data["stars"], 2)

    def test_leaderboard_ordering(self):
        # Create another user and give them more XP
        other_user = User.objects.create_user(username="pro", email="pro@ex.com", password="pw")
        pro_profile = other_user.profile
        pro_profile.xp = 1000
        pro_profile.save()

        url = reverse("leaderboard")
        response = self.client.get(url)

        # "pro" should be first
        self.assertEqual(response.data[0]["username"], "pro")
        self.assertEqual(response.data[1]["username"], "player")
