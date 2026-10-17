from unittest.mock import MagicMock, patch

import requests
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from challenges.execution import PistonExecutionService
from challenges.models import Challenge, UserProgress
from challenges.services import ChallengeService
from challenges.services.submission_service import SubmissionService

PASSED = {"passed": True, "run": {"code": 0, "stderr": "", "stdout": ""}}


class ChallengeIntegrityTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="integrity", email="i@example.com", password="pw")
        self.client.force_authenticate(user=self.user)
        self.c1 = Challenge.objects.create(
            title="L1", slug="i1", order=1, xp_reward=10, description="", initial_code="", test_code="assert True"
        )
        self.c2 = Challenge.objects.create(
            title="L2", slug="i2", order=2, xp_reward=20, description="", initial_code="", test_code="assert True"
        )

    # --- Unlock rule ---

    def test_first_level_is_unlocked(self):
        self.assertTrue(ChallengeService.is_unlocked(self.user, self.c1))

    def test_next_level_locked_until_previous_completed(self):
        self.assertFalse(ChallengeService.is_unlocked(self.user, self.c2))
        UserProgress.objects.create(user=self.user, challenge=self.c1, status=UserProgress.Status.COMPLETED)
        self.assertTrue(ChallengeService.is_unlocked(self.user, self.c2))

    def test_unpublished_levels_are_skipped(self):
        self.c1.is_published = False
        self.c1.save()
        self.assertTrue(ChallengeService.is_unlocked(self.user, self.c2))

    def test_staff_bypass_lock(self):
        self.user.is_staff = True
        self.user.save()
        self.assertTrue(ChallengeService.is_unlocked(self.user, self.c2))

    @patch("challenges.execution.PistonExecutionService.run_challenge_tests")
    def test_submit_locked_level_is_forbidden(self, mock_run):
        mock_run.return_value = PASSED
        response = self.client.post(reverse("challenge-submit", kwargs={"slug": "i2"}), {"code": "x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_run.assert_not_called()
        self.assertFalse(UserProgress.objects.filter(user=self.user, challenge=self.c2, status="COMPLETED").exists())

    @patch("challenges.execution.PistonExecutionService.run_challenge_tests")
    def test_execute_locked_level_is_forbidden(self, mock_run):
        response = self.client.post(reverse("challenge-execute", kwargs={"slug": "i2"}), {"code": "x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_run.assert_not_called()

    def test_ai_endpoints_locked_level_are_forbidden(self):
        for name in ("challenge-ai-analyze", "challenge-ai-hint", "challenge-purchase-ai-assist"):
            response = self.client.post(reverse(name, kwargs={"slug": "i2"}), {"user_code": "x"}, format="json")
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, name)

    def test_oversized_code_is_rejected(self):
        big = "x" * (PistonExecutionService.MAX_CODE_BYTES + 1)
        response = self.client.post(reverse("challenge-submit", kwargs={"slug": "i1"}), {"code": big}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Pass decision comes only from the harness ---

    @patch("challenges.execution.PistonExecutionService.run_challenge_tests")
    def test_exit_code_zero_without_harness_pass_fails(self, mock_run):
        # e.g. learner called exit(): process exit code 0 and empty stderr, but no harness token
        mock_run.return_value = {"passed": False, "run": {"code": 0, "stderr": "", "stdout": ""}}
        response = self.client.post(reverse("challenge-submit", kwargs={"slug": "i1"}), {"code": "x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(UserProgress.objects.filter(user=self.user, challenge=self.c1, status="COMPLETED").exists())

    @patch("challenges.execution.PistonExecutionService.run_challenge_tests")
    def test_execute_reports_harness_result(self, mock_run):
        mock_run.return_value = PASSED
        response = self.client.post(reverse("challenge-execute", kwargs={"slug": "i1"}), {"code": "x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["passed"])

    @patch("challenges.execution.PistonExecutionService.run_challenge_tests")
    def test_executor_unreachable_returns_503(self, mock_run):
        mock_run.side_effect = requests.exceptions.ConnectionError("down")
        response = self.client.post(reverse("challenge-submit", kwargs={"slug": "i1"}), {"code": "x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @patch("challenges.execution.PistonExecutionService.run_challenge_tests")
    def test_submit_registers_task_metadata_for_polling(self, mock_run):
        mock_run.return_value = PASSED
        with patch("learning.views.challenges._store_ai_task_meta") as store_meta:
            self.client.post(reverse("challenge-submit", kwargs={"slug": "i1"}), {"code": "x"}, format="json")
        store_meta.assert_called_once()
        self.assertEqual(store_meta.call_args.args[1:], (self.user.id, "submit"))

    # --- XP is awarded once ---

    def test_repeat_completion_awards_xp_once(self):
        start = self.user.profile.xp
        SubmissionService.process_submission_result(self.user, self.c1, passed=True)
        SubmissionService.process_submission_result(self.user, self.c1, passed=True)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.xp, start + 10)


@override_settings(EXECUTOR_URL="http://executor:8011/execute")
class ExecutorClientTests(APITestCase):
    @patch("challenges.execution.requests.post")
    def test_run_challenge_tests_sends_signed_headers_and_separate_tests(self, mock_post):
        response = MagicMock()
        response.json.return_value = {"passed": True, "run": {"code": 0}}
        mock_post.return_value = response

        with patch.dict(
            "os.environ",
            {"EXECUTOR_API_KEY": "exec-key", "EXECUTOR_SIGNING_SECRET": "exec-secret"},
        ):
            result = PistonExecutionService.run_challenge_tests("def f(): pass", "assert f() is None")

        self.assertTrue(result["passed"])
        kwargs = mock_post.call_args.kwargs
        self.assertEqual(kwargs["json"]["code"], "def f(): pass")
        self.assertEqual(kwargs["json"]["test_code"], "assert f() is None")
        self.assertEqual(kwargs["headers"]["X-Internal-API-Key"], "exec-key")
        self.assertIn("X-Internal-Signature", kwargs["headers"])

    @patch("challenges.execution.requests.post")
    def test_missing_passed_flag_counts_as_failure(self, mock_post):
        response = MagicMock()
        response.json.return_value = {"run": {"code": 0, "stderr": ""}}
        mock_post.return_value = response
        self.assertFalse(PistonExecutionService.run_challenge_tests("x = 1", "assert True")["passed"])
