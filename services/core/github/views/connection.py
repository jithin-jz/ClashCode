"""
Connection management views — CRUD for the GitHub connection.
"""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.authentication import JWTAuthentication

from ..models import GitHubConnection
from ..serializers import GitHubConnectionSerializer, GitHubConnectionUpdateSerializer

logger = logging.getLogger(__name__)


class GitHubConnectionView(APIView):
    """
    GET    /api/github-sync/connection/  — Status
    PATCH  /api/github-sync/connection/  — Update settings
    DELETE /api/github-sync/connection/  — Disconnect
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            connection = GitHubConnection.objects.get(user=request.user)
        except GitHubConnection.DoesNotExist:
            return Response({"connected": False, "connection": None})

        return Response(
            {
                "connected": True,
                "connection": GitHubConnectionSerializer(connection).data,
            }
        )

    def patch(self, request):
        try:
            connection = GitHubConnection.objects.get(user=request.user)
        except GitHubConnection.DoesNotExist:
            return Response(
                {"error": "No GitHub connection found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GitHubConnectionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        updated_fields = []

        for field in ("is_enabled", "repo_name", "repo_visibility", "include_problem_description"):
            if field in data:
                setattr(connection, field, data[field])
                updated_fields.append(field)

        if updated_fields:
            if "is_enabled" in data and data["is_enabled"]:
                connection.consecutive_failures = 0
                connection.last_error = ""
                updated_fields.extend(["consecutive_failures", "last_error"])

            connection.save(update_fields=updated_fields)

        return Response(
            {
                "message": "Connection updated.",
                "connection": GitHubConnectionSerializer(connection).data,
            }
        )

    def delete(self, request):
        deleted, _ = GitHubConnection.objects.filter(user=request.user).delete()

        if not deleted:
            return Response(
                {"error": "No GitHub connection found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        logger.info(f"GitHub disconnected: {request.user.username}")
        return Response({"message": "GitHub disconnected."})
