from django.http import HttpResponse
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from administration.permissions import IsAdminUser
from administration.serializers import AdminAuditLogSerializer
from administration.services.audit_service import AuditService
from administration.utils import _parse_int


class AdminAuditViewSet(viewsets.ViewSet):
    """
    ViewSet for administrative audit logs.
    Groups log retrieval and export actions.
    """

    permission_classes = [IsAdminUser]

    @extend_schema(
        parameters=[
            OpenApiParameter("action", str, OpenApiParameter.QUERY),
            OpenApiParameter("admin", str, OpenApiParameter.QUERY),
            OpenApiParameter("target", str, OpenApiParameter.QUERY),
            OpenApiParameter("search", str, OpenApiParameter.QUERY),
            OpenApiParameter("ordering", str, OpenApiParameter.QUERY, default="-timestamp"),
            OpenApiParameter("date_from", str, OpenApiParameter.QUERY),
            OpenApiParameter("date_to", str, OpenApiParameter.QUERY),
            OpenApiParameter("page", int, OpenApiParameter.QUERY, default=1),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY, default=50),
        ],
        responses={200: AdminAuditLogSerializer(many=True)},
        description="Retrieve administrative action logs.",
    )
    def list(self, request):
        ordering = request.query_params.get("ordering", "-timestamp")

        # Determine pagination parameters
        limit = _parse_int(request.query_params.get("limit"), 50, 1, 500)
        offset = _parse_int(request.query_params.get("offset"), 0, 0, None)
        page_size = _parse_int(request.query_params.get("page_size"), limit, min_value=1, max_value=500)
        page = _parse_int(request.query_params.get("page"), 1, min_value=1)

        if "offset" in request.query_params or "limit" in request.query_params:
            page_size = limit
            page = (offset // max(limit, 1)) + 1

        data = AuditService.get_audit_logs(
            filters=request.query_params,
            ordering=ordering,
            page=page,
            page_size=page_size,
        )

        serializer = AdminAuditLogSerializer(data["results"], many=True)
        data["results"] = serializer.data
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="export")
    @extend_schema(
        parameters=[
            OpenApiParameter("action", str, OpenApiParameter.QUERY),
            OpenApiParameter("admin", str, OpenApiParameter.QUERY),
            OpenApiParameter("target", str, OpenApiParameter.QUERY),
            OpenApiParameter("search", str, OpenApiParameter.QUERY),
            OpenApiParameter("ordering", str, OpenApiParameter.QUERY, default="-timestamp"),
        ],
        responses={200: HttpResponse},
        description="Export audit logs as CSV.",
    )
    def export(self, request):
        ordering = request.query_params.get("ordering", "-timestamp")
        csv_content = AuditService.generate_audit_logs_csv(request.query_params, ordering)
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="admin-audit-logs.csv"'
        return response
