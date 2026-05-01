import logging

from authentication.throttles import NotificationRateThrottle
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import mixins, pagination, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import FCMToken, Notification
from .serializers import (
    FCMTokenSerializer,
    NotificationListResponseSerializer,
    NotificationSerializer,
)
from .services import NotificationService

logger = logging.getLogger(__name__)


class NotificationPagination(pagination.PageNumberPagination):
    """Custom pagination to include unread_count in the response."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        unread_count = self.request.user.notifications.filter(is_read=False).count()
        return Response(
            {
                "count": self.page.paginator.count,
                "unread_count": unread_count,
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "total_pages": self.page.paginator.num_pages,
                "results": data,
            }
        )


class FCMTokenViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    ViewSet for managing FCM tokens for push notifications.
    """

    serializer_class = FCMTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FCMToken.objects.filter(user=self.request.user)

    @extend_schema(
        request=FCMTokenSerializer,
        responses={200: FCMTokenSerializer, 201: FCMTokenSerializer},
        description="Register or update an FCM token for the authenticated user.",
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fcm_token, created = NotificationService.register_fcm_token(
            user=request.user,
            token=serializer.validated_data["token"],
            device_id=serializer.validated_data.get("device_id"),
        )

        response_serializer = self.get_serializer(fcm_token)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class NotificationViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for managing user notifications with proper serialization and pagination.
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination
    throttle_classes = [NotificationRateThrottle]

    def get_queryset(self):
        """Optimized queryset with select_related for performance."""
        return (
            Notification.objects.select_related("actor", "actor__profile")
            .filter(recipient=self.request.user)
            .order_by("-created_at")
        )

    @extend_schema(
        responses={200: NotificationListResponseSerializer},
        description="List notifications for the authenticated user with pagination and unread count.",
    )
    def list(self, request, *args, **kwargs):
        # The list logic is now largely handled by the pagination_class
        return super().list(request, *args, **kwargs)

    @extend_schema(
        request=None,
        responses={200: OpenApiTypes.OBJECT},
        description="Mark all notifications as read for the authenticated user.",
    )
    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        count = NotificationService.mark_all_as_read(request.user)
        return Response({"status": "success", "marked_read": count}, status=status.HTTP_200_OK)

    @extend_schema(
        request=None,
        responses={204: None},
        description="Delete all notifications for the authenticated user.",
    )
    @action(detail=False, methods=["delete"])
    def clear_all(self, request):
        NotificationService.clear_all(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=None,
        responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
        description="Mark a specific notification as read.",
    )
    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        success = NotificationService.mark_as_read(pk, request.user)
        if not success:
            return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {"status": "success", "message": "Notification marked as read."},
            status=status.HTTP_200_OK,
        )
