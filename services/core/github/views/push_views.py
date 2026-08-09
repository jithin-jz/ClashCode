"""
Push history, stats, retry, and verify views.
"""

from django.db.models import Avg
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.authentication import JWTAuthentication

from ..models import GitHubConnection, GitHubPushLog
from ..serializers import GitHubPushLogSerializer, GitHubSyncStatsSerializer
from ..services import GitHubSyncService, GitHubTokenExpiredError
from ..tasks import push_solution_to_github


class GitHubPushHistoryView(APIView):
    """GET /api/github-sync/history/ — Paginated push history."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            connection = GitHubConnection.objects.get(user=request.user)
        except GitHubConnection.DoesNotExist:
            return Response({"results": [], "count": 0})

        page = int(request.query_params.get("page", 1))
        page_size = min(int(request.query_params.get("page_size", 20)), 50)
        offset = (page - 1) * page_size

        logs = GitHubPushLog.objects.filter(connection=connection).order_by("-created_at")[offset : offset + page_size]
        total = GitHubPushLog.objects.filter(connection=connection).count()

        return Response(
            {
                "results": GitHubPushLogSerializer(logs, many=True).data,
                "count": total,
                "page": page,
                "page_size": page_size,
                "has_next": offset + page_size < total,
            }
        )


class GitHubSyncStatsView(APIView):
    """GET /api/github-sync/stats/ — Aggregated push statistics."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            connection = GitHubConnection.objects.get(user=request.user)
        except GitHubConnection.DoesNotExist:
            return Response({"error": "No connection."}, status=status.HTTP_404_NOT_FOUND)

        logs = GitHubPushLog.objects.filter(connection=connection)

        stats = {
            "total_pushes": logs.count(),
            "success_count": logs.filter(status=GitHubPushLog.Status.SUCCESS).count(),
            "failed_count": logs.filter(status=GitHubPushLog.Status.FAILED).count(),
            "pending_count": logs.filter(
                status__in=[GitHubPushLog.Status.PENDING, GitHubPushLog.Status.IN_PROGRESS]
            ).count(),
            "avg_duration_ms": logs.filter(status=GitHubPushLog.Status.SUCCESS, duration_ms__isnull=False).aggregate(
                avg=Avg("duration_ms")
            )["avg"],
            "last_push_at": logs.filter(status=GitHubPushLog.Status.SUCCESS)
            .values_list("pushed_at", flat=True)
            .first(),
        }

        return Response(GitHubSyncStatsSerializer(stats).data)


class GitHubRetryPushView(APIView):
    """POST /api/github-sync/retry/<id>/ — Manually retry a failed push."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, log_id):
        try:
            connection = GitHubConnection.objects.get(user=request.user)
            push_log = GitHubPushLog.objects.get(id=log_id, connection=connection)
        except (GitHubConnection.DoesNotExist, GitHubPushLog.DoesNotExist):
            return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if push_log.status == GitHubPushLog.Status.SUCCESS:
            return Response({"error": "Already succeeded."}, status=status.HTTP_400_BAD_REQUEST)

        if not connection.is_enabled:
            return Response(
                {"error": "Sync is disabled. Enable it first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        push_log.status = GitHubPushLog.Status.PENDING
        push_log.error_message = ""
        push_log.save(update_fields=["status", "error_message"])

        push_solution_to_github.delay(push_log.id)

        return Response({"message": "Retry queued.", "status": "PENDING"})


class GitHubVerifyView(APIView):
    """POST /api/github-sync/verify/ — Verify token is still valid."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            connection = GitHubConnection.objects.get(user=request.user)
        except GitHubConnection.DoesNotExist:
            return Response({"error": "No connection."}, status=status.HTTP_404_NOT_FOUND)

        service = GitHubSyncService(connection)
        try:
            user_info = service.verify_token()
            return Response(
                {
                    "valid": True,
                    "github_username": user_info.get("login"),
                    "avatar_url": user_info.get("avatar_url"),
                    "rate_limit": service.check_rate_limit(),
                }
            )
        except GitHubTokenExpiredError:
            connection.is_enabled = False
            connection.last_error = "Token expired. Please reconnect."
            connection.save(update_fields=["is_enabled", "last_error"])
            return Response(
                {"valid": False, "error": "Token expired. Please reconnect."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
