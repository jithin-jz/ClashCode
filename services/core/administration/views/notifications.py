from drf_spectacular.utils import OpenApiTypes, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from administration.permissions import IsAdminUser
from administration.services.notification_service import NotificationService


class GlobalNotificationView(APIView):
    """View to send notifications to all users."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        request=inline_serializer(
            name="GlobalNotificationRequest",
            fields={
                "message": serializers.CharField(max_length=500),
                "include_staff": serializers.BooleanField(default=False),
                "reason": serializers.CharField(required=False),
            },
        ),
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
        description="Broadcast a notification to all active users.",
    )
    def post(self, request):
        # We can use a serializer for validation here as well
        class NotificationInputSerializer(serializers.Serializer):
            message = serializers.CharField(max_length=500)
            include_staff = serializers.BooleanField(default=False)
            reason = serializers.CharField(required=False, allow_blank=True)

        serializer = NotificationInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        v_data = serializer.validated_data
        success, msg, code = NotificationService.broadcast_notification(
            admin=request.user,
            message=v_data["message"],
            include_staff=v_data["include_staff"],
            reason=v_data.get("reason", ""),
            request=request,
        )

        if not success:
            return Response({"error": msg}, status=code)

        return Response({"message": msg}, status=status.HTTP_200_OK)


class BroadcastHistoryView(APIView):
    """View to retrieve broadcast history."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Retrieve broadcast history from admin audit logs.",
    )
    def get(self, request):
        rows = NotificationService.get_broadcast_history()
        return Response({"results": rows}, status=status.HTTP_200_OK)


class BroadcastResendView(APIView):
    """View to resend a previously sent broadcast."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
        description="Resend a previously sent broadcast by request id.",
    )
    def post(self, request, request_id):
        success, msg, code = NotificationService.resend_broadcast(admin=request.user, request_id=request_id, request=request)

        if not success:
            return Response({"error": msg}, status=code)

        return Response({"message": msg}, status=status.HTTP_200_OK)
