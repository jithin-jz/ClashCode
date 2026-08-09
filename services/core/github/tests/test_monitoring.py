import hashlib
import hmac
import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from github.encryption import encrypt_token
from github.metrics import GitHubSyncMetrics
from github.models import GitHubConnection, GitHubPushLog


class GitHubMetricsTest(TestCase):
    """Test the monitoring/metrics system."""

    def setUp(self):
        self.user = User.objects.create_user(username="metricsuser", password="pass123")
        self.connection = GitHubConnection.objects.create(
            user=self.user,
            github_username="metricsuser",
            access_token_encrypted=encrypt_token("ghp_test"),
            is_enabled=True,
        )
        # Create some push logs
        for i in range(5):
            GitHubPushLog.objects.create(
                connection=self.connection,
                challenge_title=f"Challenge {i}",
                challenge_slug=f"challenge-{i}",
                challenge_order=i,
                user_code=f"print({i})",
                status=GitHubPushLog.Status.SUCCESS,
                duration_ms=1000 + (i * 200),
            )
        # Add a couple of failed ones
        for i in range(2):
            GitHubPushLog.objects.create(
                connection=self.connection,
                challenge_title=f"Failed {i}",
                challenge_slug=f"failed-{i}",
                challenge_order=10 + i,
                user_code="bad code",
                status=GitHubPushLog.Status.FAILED,
                error_message="Token expired",
                duration_ms=500,
            )

    def test_dashboard_metrics_structure(self):
        """Dashboard metrics returns correct structure."""
        metrics = GitHubSyncMetrics.get_dashboard_metrics(time_window_hours=24)

        self.assertIn("pushes", metrics)
        self.assertIn("latency", metrics)
        self.assertIn("connections", metrics)
        self.assertIn("errors", metrics)
        self.assertIn("hourly_rate", metrics)

        self.assertEqual(metrics["pushes"]["success"], 5)
        self.assertEqual(metrics["pushes"]["failed"], 2)
        self.assertEqual(metrics["pushes"]["total"], 7)
        self.assertGreater(metrics["pushes"]["success_rate"], 70)

        self.assertEqual(metrics["connections"]["active"], 1)
        self.assertIsNotNone(metrics["latency"]["avg_ms"])

    def test_prometheus_export_format(self):
        """Prometheus export produces valid text format."""
        output = GitHubSyncMetrics.prometheus_export()

        self.assertIn("github_sync_connections_active", output)
        self.assertIn("github_sync_pushes_total", output)
        self.assertIn("# HELP", output)
        self.assertIn("# TYPE", output)
        # Should be text, not JSON
        self.assertNotIn("{", output.split("\n")[0])

    def test_metrics_endpoint_no_auth(self):
        """Metrics endpoint is accessible without auth (for Prometheus)."""
        client = APIClient()
        resp = client.get("/api/github-sync/metrics/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("github_sync", resp.content.decode())

    def test_dashboard_metrics_requires_staff(self):
        """Dashboard metrics requires staff access."""
        client = APIClient()
        client.force_authenticate(user=self.user)

        resp = client.get("/api/github-sync/dashboard/metrics/")
        self.assertEqual(resp.status_code, 403)

    def test_dashboard_metrics_staff_access(self):
        """Staff can access dashboard metrics."""
        staff = User.objects.create_user(username="admin", password="pass", is_staff=True)
        client = APIClient()
        client.force_authenticate(user=staff)

        resp = client.get("/api/github-sync/dashboard/metrics/?hours=12")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["time_window_hours"], 12)


class GitHubWebhookTest(TestCase):
    """Test the GitHub webhook handler."""

    def setUp(self):
        self.user = User.objects.create_user(username="webhookuser", password="pass123")
        self.connection = GitHubConnection.objects.create(
            user=self.user,
            github_username="webhookuser",
            access_token_encrypted=encrypt_token("ghp_test"),
            is_enabled=True,
        )
        self.client = APIClient()

    def _sign_payload(self, payload: dict, secret: str) -> str:
        """Generate HMAC-SHA256 signature for webhook payload."""
        body = json.dumps(payload).encode("utf-8")
        sig = hmac.new(
            key=secret.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256,
        ).hexdigest()
        return f"sha256={sig}"

    def test_webhook_rejects_without_secret_configured(self):
        """Rejects when GITHUB_WEBHOOK_SECRET is not configured."""
        with self.settings(GITHUB_WEBHOOK_SECRET=""):
            resp = self.client.post(
                "/api/github-sync/webhook/",
                data={"action": "revoked"},
                format="json",
                HTTP_X_GITHUB_EVENT="github_app_authorization",
            )
            self.assertEqual(resp.status_code, 403)

    def test_webhook_rejects_invalid_signature(self):
        """Rejects with wrong signature."""
        with self.settings(GITHUB_WEBHOOK_SECRET="real-secret"):
            resp = self.client.post(
                "/api/github-sync/webhook/",
                data={"action": "revoked", "sender": {"login": "webhookuser"}},
                format="json",
                HTTP_X_GITHUB_EVENT="github_app_authorization",
                HTTP_X_HUB_SIGNATURE_256="sha256=invalid",
            )
            self.assertEqual(resp.status_code, 403)

    def test_webhook_processes_revocation(self):
        """Valid revocation webhook disables the connection."""
        secret = "test-webhook-secret"
        payload = {
            "action": "revoked",
            "sender": {"login": "webhookuser", "id": 12345},
        }

        # Must sign the exact bytes the server will see
        body = json.dumps(payload).encode("utf-8")
        signature = (
            "sha256="
            + hmac.new(
                key=secret.encode("utf-8"),
                msg=body,
                digestmod=hashlib.sha256,
            ).hexdigest()
        )

        with self.settings(GITHUB_WEBHOOK_SECRET=secret):
            resp = self.client.post(
                "/api/github-sync/webhook/",
                data=body,
                content_type="application/json",
                HTTP_X_GITHUB_EVENT="github_app_authorization",
                HTTP_X_HUB_SIGNATURE_256=signature,
            )

        self.assertEqual(resp.status_code, 200)

        self.connection.refresh_from_db()
        self.assertFalse(self.connection.is_enabled)
        self.assertIn("revoked", self.connection.last_error.lower())


class GitHubAdminBulkRetryTest(TestCase):
    """Test admin bulk-retry action."""

    def setUp(self):
        self.admin = User.objects.create_superuser(username="superadmin", password="admin123")
        self.user = User.objects.create_user(username="bulkuser", password="pass123")
        self.connection = GitHubConnection.objects.create(
            user=self.user,
            github_username="bulkuser",
            access_token_encrypted=encrypt_token("ghp_test"),
            is_enabled=True,
        )
        # Create failed logs
        self.failed_logs = []
        for i in range(3):
            log = GitHubPushLog.objects.create(
                connection=self.connection,
                challenge_title=f"Challenge {i}",
                challenge_slug=f"challenge-{i}",
                challenge_order=i,
                user_code=f"print({i})",
                status=GitHubPushLog.Status.FAILED,
                error_message="Temporary error",
            )
            self.failed_logs.append(log)

    def test_admin_can_see_retry_action(self):
        """Admin interface shows the retry action."""
        from github.admin import GitHubConnectionAdmin

        admin_instance = GitHubConnectionAdmin(GitHubConnection, None)
        # Check actions are defined
        self.assertIn("retry_all_failed", list(admin_instance.actions))

    @patch("github.admin.push_solution_to_github.delay")
    def test_bulk_retry_requeues_failed(self, mock_delay):
        """Bulk retry action re-queues all failed pushes."""
        from django.contrib.admin.sites import AdminSite
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        from github.admin import GitHubConnectionAdmin

        factory = RequestFactory()
        request = factory.post("/admin/")
        request.user = self.admin
        # Add message storage for admin actions
        request.session = "session"
        messages = FallbackStorage(request)
        request._messages = messages

        admin_instance = GitHubConnectionAdmin(GitHubConnection, AdminSite())
        queryset = GitHubConnection.objects.filter(id=self.connection.id)

        admin_instance.retry_all_failed(request, queryset)

        # All 3 failed logs should be retried
        self.assertEqual(mock_delay.call_count, 3)

        # Status should be reset to PENDING
        for log in self.failed_logs:
            log.refresh_from_db()
            self.assertEqual(log.status, GitHubPushLog.Status.PENDING)
