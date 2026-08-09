from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from github.encryption import decrypt_token, encrypt_token
from github.models import GitHubConnection, GitHubPushLog
from github.services import (
    GitHubSyncError,
    GitHubSyncService,
    GitHubTokenExpiredError,
)
from github.tasks import push_solution_to_github


class EncryptionTest(TestCase):
    """Verify token encryption round-trips correctly."""

    def test_encrypt_decrypt_roundtrip(self):
        token = "ghp_abc123XYZ456_reallyLongTokenHere"
        encrypted = encrypt_token(token)
        decrypted = decrypt_token(encrypted)
        self.assertEqual(decrypted, token)

    def test_different_tokens_produce_different_ciphertext(self):
        enc1 = encrypt_token("token_one")
        enc2 = encrypt_token("token_two")
        self.assertNotEqual(enc1, enc2)

    def test_same_token_different_nonce(self):
        """Each encryption has a unique nonce, so ciphertext differs."""
        enc1 = encrypt_token("same_token")
        enc2 = encrypt_token("same_token")
        self.assertNotEqual(enc1, enc2)

    def test_invalid_data_raises(self):
        with self.assertRaises(Exception):
            decrypt_token(b"too_short")


class GitHubPushTaskTest(TestCase):
    """Test the Celery task."""

    def setUp(self):
        self.user = User.objects.create_user(username="taskuser", password="pass123")
        self.connection = GitHubConnection.objects.create(
            user=self.user,
            github_username="taskuser",
            access_token_encrypted=encrypt_token("ghp_test_token"),
            is_enabled=True,
        )
        self.push_log = GitHubPushLog.objects.create(
            connection=self.connection,
            challenge_title="Loops",
            challenge_slug="loops",
            challenge_order=2,
            challenge_description="Write a loop.",
            user_code="for i in range(10): print(i)",
        )

    @patch.object(GitHubSyncService, "push_solution")
    def test_successful_push(self, mock_push):
        """Success updates log, connection stats, and records duration."""
        mock_push.return_value = {
            "sha": "abc1234567890abcdef1234567890abcdef123456",
            "url": "https://github.com/taskuser/clashcode-solutions/commit/abc1234",
        }

        push_solution_to_github(self.push_log.id)

        self.push_log.refresh_from_db()
        self.connection.refresh_from_db()

        self.assertEqual(self.push_log.status, GitHubPushLog.Status.SUCCESS)
        self.assertIsNotNone(self.push_log.pushed_at)
        self.assertIsNotNone(self.push_log.duration_ms)
        self.assertGreaterEqual(self.push_log.duration_ms, 0)
        self.assertEqual(self.connection.consecutive_failures, 0)

    @patch.object(GitHubSyncService, "push_solution")
    def test_token_expired_disables_connection(self, mock_push):
        """Token expiry disables the connection."""
        mock_push.side_effect = GitHubTokenExpiredError("Token revoked")

        push_solution_to_github(self.push_log.id)

        self.push_log.refresh_from_db()
        self.connection.refresh_from_db()

        self.assertEqual(self.push_log.status, GitHubPushLog.Status.FAILED)
        self.assertFalse(self.connection.is_enabled)

    @patch.object(GitHubSyncService, "push_solution")
    def test_skips_when_disabled(self, mock_push):
        """Skips if connection disabled."""
        self.connection.is_enabled = False
        self.connection.save()

        push_solution_to_github(self.push_log.id)

        self.push_log.refresh_from_db()
        self.assertEqual(self.push_log.status, GitHubPushLog.Status.SKIPPED)
        mock_push.assert_not_called()

    @patch.object(GitHubSyncService, "push_solution")
    def test_circuit_breaker_auto_disables(self, mock_push):
        """After N consecutive failures, connection is auto-disabled."""
        mock_push.side_effect = GitHubSyncError("Server error")

        # Directly test the circuit breaker on the connection model
        for i in range(GitHubConnection.AUTO_DISABLE_THRESHOLD):
            was_disabled = self.connection.record_failure(f"Error {i}")
            if i < GitHubConnection.AUTO_DISABLE_THRESHOLD - 1:
                self.assertFalse(was_disabled)

        self.connection.refresh_from_db()
        self.assertFalse(self.connection.is_enabled)
        self.assertIn("Auto-disabled", self.connection.last_error)


class GitHubConnectionViewTest(TestCase):
    """Test REST API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(username="apiuser", password="pass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_connection_not_connected(self):
        """Returns connected=False for users without connection."""
        resp = self.client.get("/api/github-sync/connection/")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data["connected"])

    def test_get_connection_connected(self):
        """Returns connection data for connected users."""
        GitHubConnection.objects.create(
            user=self.user,
            github_username="apiuser",
            access_token_encrypted=encrypt_token("ghp_test"),
            is_enabled=True,
        )

        resp = self.client.get("/api/github-sync/connection/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["connected"])
        self.assertEqual(resp.data["connection"]["github_username"], "apiuser")
        # Token should NEVER appear in response
        self.assertNotIn("access_token", resp.data["connection"])
        self.assertNotIn("access_token_encrypted", resp.data["connection"])

    def test_patch_connection_updates_settings(self):
        """PATCH updates connection settings."""
        GitHubConnection.objects.create(
            user=self.user,
            github_username="apiuser",
            access_token_encrypted=encrypt_token("ghp_test"),
            is_enabled=True,
        )

        resp = self.client.patch(
            "/api/github-sync/connection/",
            {"is_enabled": False, "repo_visibility": "private"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data["connection"]["is_enabled"])
        self.assertEqual(resp.data["connection"]["repo_visibility"], "private")

    def test_delete_connection(self):
        """DELETE removes the connection."""
        GitHubConnection.objects.create(
            user=self.user,
            github_username="apiuser",
            access_token_encrypted=encrypt_token("ghp_test"),
        )

        resp = self.client.delete("/api/github-sync/connection/")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(GitHubConnection.objects.filter(user=self.user).exists())

    def test_history_pagination(self):
        """History endpoint supports pagination."""
        conn = GitHubConnection.objects.create(
            user=self.user,
            github_username="apiuser",
            access_token_encrypted=encrypt_token("ghp_test"),
        )
        for i in range(5):
            GitHubPushLog.objects.create(
                connection=conn,
                challenge_title=f"Challenge {i}",
                challenge_slug=f"challenge-{i}",
                challenge_order=i,
                user_code=f"print({i})",
                status=GitHubPushLog.Status.SUCCESS,
            )

        resp = self.client.get("/api/github-sync/history/?page=1&page_size=2")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 2)
        self.assertEqual(resp.data["count"], 5)
        self.assertTrue(resp.data["has_next"])

    def test_stats_endpoint(self):
        """Stats endpoint returns aggregated data."""
        conn = GitHubConnection.objects.create(
            user=self.user,
            github_username="apiuser",
            access_token_encrypted=encrypt_token("ghp_test"),
        )
        GitHubPushLog.objects.create(
            connection=conn,
            challenge_title="Test",
            challenge_slug="test",
            user_code="x=1",
            status=GitHubPushLog.Status.SUCCESS,
            duration_ms=1500,
        )

        resp = self.client.get("/api/github-sync/stats/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["total_pushes"], 1)
        self.assertEqual(resp.data["success_count"], 1)
        self.assertEqual(resp.data["avg_duration_ms"], 1500)
