from rest_framework import serializers

from .models import AdminAuditLog, AdminNote, AdminReport


class AdminStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_sessions = serializers.IntegerField()
    oauth_logins = serializers.IntegerField()
    total_gems = serializers.IntegerField()


class AdminAuditLogSerializer(serializers.ModelSerializer):
    admin = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()

    class Meta:
        model = AdminAuditLog
        fields = [
            "admin",
            "action",
            "target",
            "details",
            "timestamp",
            "request_id",
            "actor_ip",
        ]

    def get_admin(self, obj):
        return obj.admin_username or (obj.admin.username if obj.admin else "System")

    def get_target(self, obj):
        return obj.target_username or (obj.target_user.username if obj.target_user else "System")


class AdminNoteSerializer(serializers.ModelSerializer):
    admin = serializers.SerializerMethodField()

    class Meta:
        model = AdminNote
        fields = ["id", "admin", "body", "is_pinned", "created_at", "updated_at"]

    def get_admin(self, obj):
        return obj.admin.username


class AdminReportSerializer(serializers.ModelSerializer):
    target = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    resolved_by = serializers.SerializerMethodField()

    class Meta:
        model = AdminReport
        fields = [
            "id",
            "title",
            "summary",
            "category",
            "priority",
            "status",
            "context",
            "target",
            "created_by",
            "resolved_by",
            "created_at",
            "updated_at",
            "resolved_at",
        ]

    def get_target(self, obj):
        return obj.target_user.username

    def get_created_by(self, obj):
        return obj.created_by.username if obj.created_by else "System"

    def get_resolved_by(self, obj):
        return obj.resolved_by.username if obj.resolved_by else None


class ChallengeAnalyticsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    attempts = serializers.IntegerField()
    completions = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    abandonment_rate = serializers.FloatField()
    average_time_seconds = serializers.FloatField()
    avg_stars = serializers.FloatField()
    is_personalized = serializers.BooleanField()


class StoreItemSalesSerializer(serializers.Serializer):
    name = serializers.CharField()
    category = serializers.CharField()
    cost = serializers.IntegerField()
    sales = serializers.IntegerField()
    revenue = serializers.IntegerField()


class StoreAnalyticsSerializer(serializers.Serializer):
    items = StoreItemSalesSerializer(many=True)
    total_xp_spent = serializers.IntegerField()


class SystemIntegritySerializer(serializers.Serializer):
    users = serializers.IntegerField()
    challenges = serializers.IntegerField()
    store_items = serializers.IntegerField()
    notifications = serializers.IntegerField()
    audit_logs = serializers.IntegerField()


class UserEngagementAnalyticsSerializer(serializers.Serializer):
    daily_growth = serializers.ListField(child=serializers.DictField())
    active_users_24h = serializers.IntegerField()
    auth_distribution = serializers.ListField(child=serializers.DictField())
    top_users = serializers.ListField(child=serializers.DictField())


class UltimateAnalyticsSerializer(serializers.Serializer):
    overview = serializers.DictField()
    growth_trends = serializers.ListField(child=serializers.DictField())
    economy_pulse = serializers.DictField()
    top_challenges = serializers.ListField(child=serializers.DictField())
    top_items = serializers.ListField(child=serializers.DictField())
    community_leaders = serializers.ListField(child=serializers.DictField())
    system_health = serializers.DictField(required=False)


class AdminReportCreateSerializer(serializers.Serializer):
    target = serializers.CharField()
    title = serializers.CharField(max_length=200)
    summary = serializers.CharField(max_length=2000)
    category = serializers.CharField(required=False, default="GENERAL")
    priority = serializers.ChoiceField(
        choices=[choice for choice, _ in AdminReport.Priority.choices], default="MEDIUM"
    )
    context = serializers.JSONField(required=False, default=dict)


class NotificationCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    message = serializers.CharField(max_length=2000)
    category = serializers.CharField(required=False, default="SYSTEM")
    persistent = serializers.BooleanField(required=False, default=True)


class AdminReportUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[c for c, _ in AdminReport.Status.choices], required=False)
    priority = serializers.ChoiceField(choices=[c for c, _ in AdminReport.Priority.choices], required=False)
    summary = serializers.CharField(max_length=2000, required=False)


class AdminUserBlockSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class AdminUserRoleUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["user", "staff", "superuser"])


class AdminUserBulkActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["block", "unblock"])
    usernames = serializers.ListField(child=serializers.CharField())


class AdminUserNoteCreateSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=2000)
    is_pinned = serializers.BooleanField(required=False, default=False)
