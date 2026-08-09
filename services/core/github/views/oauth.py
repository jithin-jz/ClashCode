"""
OAuth views — connect URL and code exchange.
"""

import logging
import secrets

import requests as http_requests
from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.authentication import JWTAuthentication

from ..encryption import encrypt_token
from ..models import GitHubConnection
from ..serializers import (
    GitHubConnectionSerializer,
    GitHubConnectSerializer,
    GitHubOAuthURLSerializer,
)
from ..services import exchange_github_code, get_github_oauth_url

logger = logging.getLogger(__name__)


class GitHubOAuthURLView(APIView):
    """GET /api/github-sync/connect/url/ — Returns GitHub OAuth URL."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        state = secrets.token_urlsafe(32)
        cache.set(f"github:oauth_state:{request.user.id}", state, timeout=600)

        url = get_github_oauth_url(state=state)
        return Response(GitHubOAuthURLSerializer({"url": url}).data)


class GitHubConnectView(APIView):
    """POST /api/github-sync/connect/ — Exchange code, create connection."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GitHubConnectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]
        user = request.user

        # Verify OAuth state
        expected_state = cache.get(f"github:oauth_state:{user.id}")
        provided_state = request.data.get("state", "")
        if expected_state and provided_state and expected_state != provided_state:
            return Response(
                {"error": "Invalid OAuth state. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cache.delete(f"github:oauth_state:{user.id}")

        # Exchange code for token
        token_data = exchange_github_code(code)

        if "error" in token_data:
            logger.warning(f"GitHub OAuth exchange failed for {user.username}: {token_data}")
            return Response(
                {"error": "Failed to connect GitHub. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        access_token = token_data.get("access_token")
        if not access_token:
            return Response(
                {"error": "No access token received from GitHub."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify token and get username
        user_resp = http_requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=10,
        )

        if user_resp.status_code != 200:
            return Response(
                {"error": "Failed to verify GitHub token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        github_user = user_resp.json()
        github_username = github_user.get("login", "")

        # Encrypt and store
        encrypted_token = encrypt_token(access_token)

        connection, created = GitHubConnection.objects.update_or_create(
            user=user,
            defaults={
                "github_username": github_username,
                "access_token_encrypted": encrypted_token,
                "is_enabled": True,
                "last_error": "",
                "consecutive_failures": 0,
            },
        )

        action = "connected" if created else "reconnected"
        logger.info(f"GitHub {action}: {user.username} → {github_username}")

        return Response(
            {
                "message": f"GitHub {action} successfully!",
                "connection": GitHubConnectionSerializer(connection).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
