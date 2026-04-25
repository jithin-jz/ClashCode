from django.core.paginator import Paginator
from rest_framework import viewsets, permissions, status, mixins, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    inline_serializer,
)
from authentication.throttles import NotificationRateThrottle
from .models import Notification, FCMToken
from .serializers import NotificationSerializer, FCMTokenSerializer


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
        token = request.data.get("token")
        device_id = request.data.get("device_id")

        if not token:
            return Response(
                {"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Use token as the primary lookup to avoid IntegrityError if device_id changes
            fcm_token, created = FCMToken.objects.update_or_create(
                token=token, defaults={"user": request.user, "device_id": device_id}
            )

            serializer = self.get_serializer(fcm_token)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for managing user notifications.
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [NotificationRateThrottle]

    def get_queryset(self):
        return Notification.objects.select_related("actor", "actor__profile").filter(
            recipient=self.request.user
        )

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, OpenApiParameter.QUERY, default=1),
            OpenApiParameter("page_size", int, OpenApiParameter.QUERY, default=50),
        ],
        responses={
            200: inline_serializer(
                name="NotificationListResponse",
                fields={
                    "count": serializers.IntegerField(),
                    "unread_count": serializers.IntegerField(),
                    "page": serializers.IntegerField(),
                    "page_size": serializers.IntegerField(),
                    "total_pages": serializers.IntegerField(),
                    "results": NotificationSerializer(many=True),
                },
            )
        },
        description="List notifications for the authenticated user with pagination metadata.",
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().order_by("-created_at")
        unread_count = queryset.filter(is_read=False).count()

        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(request.query_params.get("page_size", 50))
        except (TypeError, ValueError):
            page_size = 50
        page_size = min(max(page_size, 1), 100)

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        serializer = self.get_serializer(
            page_obj.object_list,
            many=True,
            context={"request": request},
        )

        return Response(
            {
                "count": paginator.count,
                "unread_count": unread_count,
                "page": page_obj.number,
                "page_size": page_size,
                "total_pages": paginator.num_pages,
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=None,
        responses={200: OpenApiTypes.OBJECT},
        description="Mark all notifications as read for the authenticated user.",
    )
    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"status": "marked all read"}, status=status.HTTP_200_OK)

    @extend_schema(
        request=None,
        responses={204: None},
        description="Delete all notifications for the authenticated user.",
    )
    @action(detail=False, methods=["delete"])
    def clear_all(self, request):
        self.get_queryset().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=None,
        responses={200: OpenApiTypes.OBJECT},
        description="Mark a specific notification as read.",
    )
    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"status": "marked read"}, status=status.HTTP_200_OK)
