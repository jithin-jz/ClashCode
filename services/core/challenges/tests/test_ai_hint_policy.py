import os
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from challenges.models import Challenge, UserProgress


class AIHintPolicyTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="hintuser", password="password")
        self.client.force_authenticate(user=self.user)

        self.challenge = Challenge.objects.create(
            title="Hint Challenge",
            slug="hint-challenge",
            description="Write a function.",
            initial_code="def solve(x):\n    pass",
            test_code="assert True",
            order=1,
            xp_reward=10,
        )

        self.progress, _ = UserProgress.objects.get_or_create(user=self.user, challenge=self.challenge)

        self.url = f"/api/challenges/{self.challenge.slug}/ai-hint/"
        os.environ["INTERNAL_API_KEY"] = "test-internal-key"
        os.environ["AI_SERVICE_URL"] = "http://ai:8002"
        cache.clear()

    def test_rejects_non_integer_hint_level(self):
        self.progress.ai_hints_purchased = 3
        self.progress.save(update_fields=["ai_hints_purchased"])

        response = self.client.post(
            self.url,
            {"user_code": "print('x')", "hint_level": "abc"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("hint_level", response.data["error"])

    def test_rejects_hint_level_above_three(self):
        self.progress.ai_hints_purchased = 3
        self.progress.save(update_fields=["ai_hints_purchased"])

        response = self.client.post(
            self.url,
            {"user_code": "print('x')", "hint_level": 4},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("between 1 and 3", response.data["error"])

    @patch("requests.post")
    def test_returns_cached_hint_for_same_level(self, mock_post):
        self.progress.ai_hints_purchased = 1
        self.progress.save(update_fields=["ai_hints_purchased"])

        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {"hint": "Focus on the loop invariant."}
        mock_post.return_value = fake_response

        first = self.client.post(
            self.url,
            {"user_code": "print('x')", "hint_level": 1},
            format="json",
        )
        second = self.client.post(
            self.url,
            {"user_code": "print('x')", "hint_level": 1},
            format="json",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data["hint"], "Focus on the loop invariant.")
        self.assertEqual(second.data["hint"], "Focus on the loop invariant.")
        self.assertTrue(second.data.get("cached", False))
        self.assertEqual(mock_post.call_count, 1)
