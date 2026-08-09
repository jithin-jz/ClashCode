"""
GitHub Webhook handler for token/app revocation events.

GitHub sends webhooks when:
1. A user revokes the OAuth app authorization
2. A user uninstalls the GitHub App
3. The OAuth app is suspended

This lets us proactively disable connections instead of waiting
for a push to fail with 401.

Setup:
1. In your GitHub OAuth App settings → Webhooks
2. Set URL: https://your-domain.com/api/github-sync/webhook/
3. Set secret: Use GITHUB_WEBHOOK_SECRET env var
4. Select events: "GitHub App authorization" or "Authorization"
"""

import hashlib
import hmac
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GitHubConnection

logger = logging.getLogger(__name__)


class GitHubWebhookView(APIView):
    """
    POST /api/github-sync/webhook/

    Receives GitHub webhook events for authorization revocation.
    Secured via HMAC-SHA256 signature verification.
    """

    authentication_classes = []  # No JWT — GitHub sends this
    permission_classes = [AllowAny]

    def post(self, request):
        # ─── Verify webhook signature ────────────────────────────────
        secret = getattr(settings, "GITHUB_WEBHOOK_SECRET", "")
        if not secret:
            logger.warning("GITHUB_WEBHOOK_SECRET not configured. Rejecting webhook.")
            return Response(status=status.HTTP_403_FORBIDDEN)

        signature_header = request.META.get("HTTP_X_HUB_SIGNATURE_256", "")
        if not self._verify_signature(request.body, secret, signature_header):
            logger.warning("Invalid webhook signature. Rejecting.")
            return Response(status=status.HTTP_403_FORBIDDEN)

        # ─── Process event ───────────────────────────────────────────
        event_type = request.META.get("HTTP_X_GITHUB_EVENT", "")
        payload = request.data

        if event_type == "github_app_authorization":
            return self._handle_authorization_event(payload)

        if event_type == "installation":
            return self._handle_installation_event(payload)

        # Unknown event — acknowledge but ignore
        logger.debug(f"Ignoring GitHub webhook event: {event_type}")
        return Response({"status": "ignored"})

    def _handle_authorization_event(self, payload: dict) -> Response:
        """
        Handle OAuth app authorization revocation.
        Payload contains: action, sender (the user who revoked).
        """
        action = payload.get("action", "")

        if action != "revoked":
            return Response({"status": "ignored", "action": action})

        sender = payload.get("sender", {})
        github_username = sender.get("login", "")

        if not github_username:
            logger.warning("Revocation webhook missing sender info.")
            return Response({"status": "error"}, status=status.HTTP_400_BAD_REQUEST)

        # Find and disable the connection
        try:
            connection = GitHubConnection.objects.get(
                github_username=github_username,
                is_enabled=True,
            )
            connection.is_enabled = False
            connection.last_error = "OAuth authorization revoked by user on GitHub."
            connection.save(update_fields=["is_enabled", "last_error"])

            logger.info(
                f"GitHub authorization revoked for {connection.user.username} "
                f"(GitHub: {github_username}). Connection disabled proactively."
            )

            # Notify user
            from .tasks import _notify_user_sync_failed

            _notify_user_sync_failed(
                connection.user.id,
                "Your GitHub authorization was revoked. Please reconnect to resume auto-sync.",
            )

        except GitHubConnection.DoesNotExist:
            logger.debug(f"Revocation webhook for unknown user: {github_username}")

        return Response({"status": "processed"})

    def _handle_installation_event(self, payload: dict) -> Response:
        """Handle GitHub App installation removal (if using GitHub Apps)."""
        action = payload.get("action", "")

        if action not in ("deleted", "suspend"):
            return Response({"status": "ignored"})

        # Disable all connections for the affected accounts
        installation = payload.get("installation", {})
        account = installation.get("account", {})
        github_username = account.get("login", "")

        if github_username:
            updated = GitHubConnection.objects.filter(
                github_username=github_username,
                is_enabled=True,
            ).update(
                is_enabled=False,
                last_error=f"GitHub App {action}d. Please reinstall to resume sync.",
            )

            if updated:
                logger.info(f"Disabled {updated} connection(s) for {github_username} (app {action}d).")

        return Response({"status": "processed"})

    @staticmethod
    def _verify_signature(payload_body: bytes, secret: str, signature_header: str) -> bool:
        """
        Verify the HMAC-SHA256 signature from GitHub.
        Constant-time comparison to prevent timing attacks.
        """
        if not signature_header:
            return False

        if not signature_header.startswith("sha256="):
            return False

        expected_signature = signature_header[7:]  # Strip "sha256=" prefix

        computed = hmac.new(
            key=secret.encode("utf-8"),
            msg=payload_body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(computed, expected_signature)
