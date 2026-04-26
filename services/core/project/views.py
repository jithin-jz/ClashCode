from celery.result import AsyncResult
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView


class ServiceIndexView(APIView):
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Basic index for the core service and local gateway routes.",
    )
    def get(self, request):
        return Response(
            {
                "service": "core",
                "status": "ok",
                "docs": "/api/docs/",
                "health": "/health/",
                "api_root": "/api/",
            },
            status=status.HTTP_200_OK,
        )


class TaskStatusView(APIView):
    """
    Check the status of a Celery task by its task_id.
    Only accessible by admin/staff users.

    GET /api/tasks/<task_id>/status/
    """

    permission_classes = [IsAdminUser]

    @extend_schema(
        parameters=[OpenApiParameter("task_id", str, OpenApiParameter.PATH)],
        responses={
            200: inline_serializer(
                name="TaskStatusResponse",
                fields={
                    "task_id": serializers.CharField(),
                    "status": serializers.CharField(),
                    "result": serializers.JSONField(allow_null=True),
                    "traceback": serializers.CharField(allow_null=True),
                    "date_done": serializers.CharField(allow_null=True),
                },
            )
        },
        description="Check the status and result of a specific Celery task by its unique ID.",
    )
    def get(self, request, task_id):
        result = AsyncResult(task_id)

        response_data = {
            "task_id": task_id,
            "status": result.status,
            "result": None,
            "traceback": None,
            "date_done": None,
        }

        if result.ready():
            if result.successful():
                response_data["result"] = result.result
            else:
                response_data["result"] = str(result.result)
                response_data["traceback"] = result.traceback

            response_data["date_done"] = str(result.date_done) if result.date_done else None

        return Response(response_data, status=status.HTTP_200_OK)


class TaskResultsListView(APIView):
    """
    List recent Celery task results from the database.
    Only accessible by admin/staff users.

    GET /api/tasks/results/?limit=25&status=SUCCESS
    """

    permission_classes = [IsAdminUser]

    @extend_schema(
        parameters=[
            OpenApiParameter("limit", int, OpenApiParameter.QUERY, default=25),
            OpenApiParameter("status", str, OpenApiParameter.QUERY),
            OpenApiParameter("task_name", str, OpenApiParameter.QUERY),
        ],
        responses={
            200: inline_serializer(
                name="TaskResultsListResponse",
                fields={
                    "count": serializers.IntegerField(),
                    "results": serializers.ListField(child=serializers.DictField()),
                },
            )
        },
        description="Retrieve a list of recent task results stored in the database, with optional filtering by status or task name.",
    )
    def get(self, request):
        from django_celery_results.models import TaskResult

        try:
            limit = min(int(request.query_params.get("limit", 25)), 100)
        except (ValueError, TypeError):
            limit = 25

        status_filter = request.query_params.get("status")
        task_name_filter = request.query_params.get("task_name")

        qs = TaskResult.objects.all().order_by("-date_done")

        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        if task_name_filter:
            qs = qs.filter(task_name__icontains=task_name_filter)

        results = qs[:limit]

        data = [
            {
                "task_id": r.task_id,
                "task_name": r.task_name,
                "status": r.status,
                "result": r.result,
                "date_done": str(r.date_done),
                "date_created": (str(r.date_created) if hasattr(r, "date_created") else None),
                "worker": r.worker,
                "traceback": r.traceback[:500] if r.traceback else None,
            }
            for r in results
        ]

        return Response(
            {
                "count": len(data),
                "results": data,
            },
            status=status.HTTP_200_OK,
        )
