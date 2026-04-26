from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, OpenApiTypes
from .models import Notification, FCMToken
from users.serializers import UserSummarySerializer
from project.media import build_file_url

class FCMTokenSerializer(serializers.ModelSerializer):
    """Serializer for registering and updating FCM tokens."""
    class Meta:
        model = FCMToken
        fields = ["token", "device_id", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {
            "token": {"validators": []}  # Remove UniqueValidator to allow upserts
        }


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for individual notification records."""
    actor = UserSummarySerializer(read_only=True)
    target_preview = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ["id", "actor", "verb", "target_preview", "is_read", "created_at"]
        read_only_fields = ["id", "actor", "verb", "target_preview", "is_read", "created_at"]

    @extend_schema_field(OpenApiTypes.URI)
    def get_target_preview(self, obj):
        """Returns a preview image URL for the target object if available."""
        if not obj.target:
            return None
            
        # Check common image fields in target models
        media_field = None
        if hasattr(obj.target, "image") and obj.target.image:
            media_field = obj.target.image
        elif hasattr(obj.target, "avatar") and obj.target.avatar:
            media_field = obj.target.avatar
        elif hasattr(obj.target, "thumbnail") and obj.target.thumbnail:
            media_field = obj.target.thumbnail
            
        if media_field:
            return build_file_url(media_field, self.context.get("request"))
        return None


class NotificationListResponseSerializer(serializers.Serializer):
    """Serializer for the paginated notification list response with unread count."""
    count = serializers.IntegerField(help_text="Total number of notifications.")
    unread_count = serializers.IntegerField(help_text="Number of unread notifications.")
    page = serializers.IntegerField(help_text="Current page number.")
    page_size = serializers.IntegerField(help_text="Number of items per page.")
    total_pages = serializers.IntegerField(help_text="Total number of pages.")
    results = NotificationSerializer(many=True, help_text="List of notification objects.")
