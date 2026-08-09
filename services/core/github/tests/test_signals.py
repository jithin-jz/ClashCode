from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from challenges.models import Challenge, UserProgress
from github.encryption import encrypt_token
from github.models import GitHubConnection, GitHubPushLog


class GitHubSyncSignalTest(TestCase):
    """Test that the signal correctly queues pushes on challenge completion."""

    def setUp(self):
        self.user = User.objects.create_user(username="testdev", password="pass123")
        self.challenge = Challenge.objects.create(
            title="Variables 101",
            slug="variables-101",
            description="Learn about variables in Python.",
            initial_code="x = 0",
            test_code="assert x == 42",
            order=1,
        )
        self.connection = GitHubConnection.objects.create(
            user=self.user,
            github_username="testdev",
            access_token_encrypted=encrypt_token("ghp_fake_token_123"),
            repo_name="clashcode-solutions",
            is_enabled=True,
        )

    def tearDown(self):
        cache.clear()

    @patch("github.tasks.push_solution_to_github.delay")
    def test_signal_queues_push_on_completion(self, mock_delay):
        """Completion with cached code queues a push."""
        cache.set(
            f"github_sync:last_code:{self.user.id}:{self.challenge.id}",
            "x = 42",
            timeout=300,
        )

        UserProgress.objects.create(
            user=self.user,
            challenge=self.challenge,
            status=UserProgress.Status.COMPLETED,
        )

        self.assertTrue(mock_delay.called)
        push_log = GitHubPushLog.objects.get(connection=self.connection)
        self.assertEqual(push_log.challenge_slug, "variables-101")
        self.assertEqual(push_log.user_code, "x = 42")
        self.assertEqual(push_log.challenge_description, "Learn about variables in Python.")
        self.assertEqual(push_log.status, GitHubPushLog.Status.PENDING)

    @patch("github.tasks.push_solution_to_github.delay")
    def test_signal_skips_when_no_connection(self, mock_delay):
        """No push if user has no GitHub connection."""
        self.connection.delete()

        cache.set(
            f"github_sync:last_code:{self.user.id}:{self.challenge.id}",
            "x = 42",
            timeout=300,
        )

        UserProgress.objects.create(
            user=self.user,
            challenge=self.challenge,
            status=UserProgress.Status.COMPLETED,
        )

        mock_delay.assert_not_called()

    @patch("github.tasks.push_solution_to_github.delay")
    def test_signal_skips_when_disabled(self, mock_delay):
        """No push if connection disabled."""
        self.connection.is_enabled = False
        self.connection.save()

        cache.set(
            f"github_sync:last_code:{self.user.id}:{self.challenge.id}",
            "x = 42",
            timeout=300,
        )

        UserProgress.objects.create(
            user=self.user,
            challenge=self.challenge,
            status=UserProgress.Status.COMPLETED,
        )

        mock_delay.assert_not_called()

    @patch("github.tasks.push_solution_to_github.delay")
    def test_signal_skips_duplicate(self, mock_delay):
        """No duplicate push for same challenge."""
        GitHubPushLog.objects.create(
            connection=self.connection,
            challenge_title=self.challenge.title,
            challenge_slug=self.challenge.slug,
            challenge_order=self.challenge.order,
            user_code="x = 42",
            status=GitHubPushLog.Status.SUCCESS,
        )

        cache.set(
            f"github_sync:last_code:{self.user.id}:{self.challenge.id}",
            "x = 42",
            timeout=300,
        )

        UserProgress.objects.create(
            user=self.user,
            challenge=self.challenge,
            status=UserProgress.Status.COMPLETED,
        )

        mock_delay.assert_not_called()

    @patch("github.tasks.push_solution_to_github.delay")
    def test_signal_skips_non_completed(self, mock_delay):
        """No push for UNLOCKED status."""
        UserProgress.objects.create(
            user=self.user,
            challenge=self.challenge,
            status=UserProgress.Status.UNLOCKED,
        )

        mock_delay.assert_not_called()

    @patch("github.tasks.push_solution_to_github.delay")
    def test_language_detection_javascript(self, mock_delay):
        """JavaScript code is detected correctly."""
        cache.set(
            f"github_sync:last_code:{self.user.id}:{self.challenge.id}",
            "const x = 42;\nconsole.log(x);",
            timeout=300,
        )

        UserProgress.objects.create(
            user=self.user,
            challenge=self.challenge,
            status=UserProgress.Status.COMPLETED,
        )

        push_log = GitHubPushLog.objects.get(connection=self.connection)
        self.assertEqual(push_log.language, "javascript")
