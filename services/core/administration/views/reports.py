from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response

from administration.permissions import IsAdminUser
from administration.serializers import (
    AdminReportCreateSerializer,
    AdminReportSerializer,
    AdminReportUpdateSerializer,
)
from administration.services.report_service import ReportService


class AdminReportViewSet(viewsets.ViewSet):
    """
    ViewSet for managing administrative reports.
    Uses Service Layer for business logic and Serializers for validation.
    """

    permission_classes = [IsAdminUser]
    lookup_field = "report_id"

    @extend_schema(
        parameters=[
            OpenApiParameter("status", str, OpenApiParameter.QUERY),
            OpenApiParameter("priority", str, OpenApiParameter.QUERY),
            OpenApiParameter("target", str, OpenApiParameter.QUERY),
        ],
        responses={200: AdminReportSerializer(many=True)},
        description="List reports queue with optional status, priority, and target filters.",
    )
    def list(self, request):
        status_filter = request.query_params.get("status")
        priority = request.query_params.get("priority")
        target = request.query_params.get("target")

        reports = ReportService.list_reports(status_filter=status_filter, priority=priority, target_username=target)
        return Response(AdminReportSerializer(reports, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(
        request=AdminReportCreateSerializer,
        responses={201: AdminReportSerializer, 400: OpenApiParameter},
        description="Create a new admin report for a specific user.",
    )
    def create(self, request):
        serializer = AdminReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        report = ReportService.create_report(
            created_by=request.user,
            target_username=validated_data["target"],
            title=validated_data["title"],
            summary=validated_data["summary"],
            category=validated_data.get("category"),
            priority=validated_data.get("priority"),
            context=validated_data.get("context"),
            request=request,
        )

        return Response(AdminReportSerializer(report).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=AdminReportUpdateSerializer,
        responses={
            200: AdminReportSerializer,
            400: OpenApiParameter,
            404: OpenApiParameter,
        },
        description="Update a report queue item.",
    )
    def partial_update(self, request, report_id=None):
        serializer = AdminReportUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report = ReportService.update_report(
            admin=request.user,
            report_id=report_id,
            updates=serializer.validated_data,
            request=request,
        )

        return Response(AdminReportSerializer(report).data, status=status.HTTP_200_OK)
