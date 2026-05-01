from django.http import StreamingHttpResponse
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.serializers import UserSerializer

from administration.permissions import IsAdminUser
from administration.serializers import (
    AdminAuditLogSerializer,
    AdminNoteSerializer,
    AdminReportSerializer,
    AdminUserBlockSerializer,
    AdminUserBulkActionSerializer,
    AdminUserNoteCreateSerializer,
    AdminUserRoleUpdateSerializer,
)
from administration.services.user_service import UserService
from administration.utils import _parse_int


class AdminUserViewSet(viewsets.ViewSet):
    """
    ViewSet for administrative user management.
    Groups all user-related admin actions with Service Layer and Serializer validation.
    """

    permission_classes = [IsAdminUser]
    lookup_field = "username"

    @extend_schema(
        parameters=[
            OpenApiParameter("search", str, OpenApiParameter.QUERY),
            OpenApiParameter("role", str, OpenApiParameter.QUERY, enum=["user", "staff", "superuser"]),
            OpenApiParameter("status", str, OpenApiParameter.QUERY, enum=["active", "blocked"]),
            OpenApiParameter("page", int, OpenApiParameter.QUERY, default=1),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY, default=25),
        ],
        responses={
            200: inline_serializer(
                name="AdminUserListResponse",
                fields={
                    "count": serializers.IntegerField(),
                    "page": serializers.IntegerField(),
                    "page_size": serializers.IntegerField(),
                    "total_pages": serializers.IntegerField(),
                    "results": UserSerializer(many=True),
                },
            ),
        },
        description="List all users with filtering and pagination.",
    )
    def list(self, request):
        page = _parse_int(request.query_params.get("page"), 1, min_value=1)
        page_size = _parse_int(request.query_params.get("page_size"), 25, min_value=1, max_value=100)

        data = UserService.list_users(
            admin_user=request.user,
            filters=request.query_params,
            page=page,
            page_size=page_size,
        )

        serialized = UserSerializer(data["results"], many=True, context={"request": request}).data
        data["results"] = serialized

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        description="Retrieve an admin drill-down view of a user.",
    )
    def retrieve(self, request, username=None):
        data = UserService.get_user_details(request.user, username)
        target = data.pop("target")
        user_data = UserSerializer(target, context={"request": request}).data

        return Response(
            {
                "user": user_data,
                "role": data["role"],
                "summary": data["summary"],
                "recent_completions": data["recent_completions"],
                "recent_purchases": data["recent_purchases"],
                "notes": AdminNoteSerializer(data["notes"], many=True).data,
                "reports": AdminReportSerializer(data["reports"], many=True).data,
                "audit_logs": AdminAuditLogSerializer(data["audit_logs"], many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        parameters=[OpenApiParameter("reason", str, OpenApiParameter.QUERY)],
        responses={
            200: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        description="Permanently delete a user account (Soft-Delete).",
    )
    def destroy(self, request, username=None):
        reason = (request.query_params.get("reason") or "").strip()
        message = UserService.soft_delete_user(
            username=username, admin_user=request.user, reason=reason, request=request
        )
        return Response({"message": message}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="toggle-block")
    @extend_schema(
        request=AdminUserBlockSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        description="Toggle a user's active status.",
    )
    def toggle_block(self, request, username=None):
        serializer = AdminUserBlockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message, is_active = UserService.toggle_user_block(
            username=username,
            admin_user=request.user,
            reason=serializer.validated_data.get("reason", ""),
            request=request,
        )

        return Response({"message": message, "is_active": is_active}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"], url_path="role")
    @extend_schema(
        request=AdminUserRoleUpdateSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        description="Update a user's role.",
    )
    def update_role(self, request, username=None):
        serializer = AdminUserRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = UserService.update_user_role(
            admin_user=request.user,
            username=username,
            new_role=serializer.validated_data["role"],
            request=request,
        )
        return Response(
            {"message": message, "role": serializer.validated_data["role"]},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="bulk")
    @extend_schema(
        request=AdminUserBulkActionSerializer,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
        description="Perform bulk block or unblock actions.",
    )
    def bulk_action(self, request):
        serializer = AdminUserBulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = UserService.bulk_update_user_status(
            admin_user=request.user,
            usernames=serializer.validated_data["usernames"],
            action=serializer.validated_data["action"],
            request=request,
        )
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="export")
    @extend_schema(
        parameters=[
            OpenApiParameter("search", str, OpenApiParameter.QUERY),
            OpenApiParameter("role", str, OpenApiParameter.QUERY),
            OpenApiParameter("status", str, OpenApiParameter.QUERY),
        ],
        responses={200: OpenApiTypes.BINARY},
        description="Export the current user list filters as CSV.",
    )
    def export(self, request):
        response = StreamingHttpResponse(
            UserService.generate_user_export_csv(request.user, request.query_params),
            content_type="text/csv",
        )
        response["Content-Disposition"] = 'attachment; filename="admin-users.csv"'
        return response

    @action(detail=True, methods=["get", "post"], url_path="notes")
    @extend_schema(
        request=AdminUserNoteCreateSerializer,
        responses={200: AdminNoteSerializer(many=True), 201: AdminNoteSerializer},
        description="List or create internal admin notes for a user.",
    )
    def notes(self, request, username=None):
        if request.method == "GET":
            notes = UserService.get_user_notes(username)
            return Response(AdminNoteSerializer(notes, many=True).data, status=status.HTTP_200_OK)

        serializer = AdminUserNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        note = UserService.create_user_note(
            admin_user=request.user,
            username=username,
            body=serializer.validated_data["body"],
            is_pinned=serializer.validated_data["is_pinned"],
            request=request,
        )
        return Response(AdminNoteSerializer(note).data, status=status.HTTP_201_CREATED)
