from django.urls import path

from .views import (
    AdminAuditViewSet,
    AdminReportViewSet,
    AdminStatsView,
    AdminUserViewSet,
    BroadcastHistoryView,
    BroadcastResendView,
    ChallengeAnalyticsView,
    GlobalNotificationView,
    StoreAnalyticsView,
    StoreItemDuplicateView,
    SystemHealthView,
    SystemIntegrityView,
    UltimateAnalyticsView,
    UserEngagementAnalyticsView,
)

urlpatterns = [
    path("stats/", AdminStatsView.as_view(), name="admin_stats"),
    path(
        "analytics/challenges/",
        ChallengeAnalyticsView.as_view(),
        name="admin_challenge_analytics",
    ),
    path("analytics/store/", StoreAnalyticsView.as_view(), name="admin_store_analytics"),
    path(
        "analytics/engagement/",
        UserEngagementAnalyticsView.as_view(),
        name="admin_engagement_analytics",
    ),
    path(
        "analytics/ultimate/",
        UltimateAnalyticsView.as_view(),
        name="admin_ultimate_analytics",
    ),
    # Audit ViewSet
    path(
        "audit-logs/",
        AdminAuditViewSet.as_view({"get": "list"}),
        name="admin_audit_logs",
    ),
    path(
        "audit-logs/export/",
        AdminAuditViewSet.as_view({"get": "export"}),
        name="admin_audit_export",
    ),
    path(
        "notifications/history/",
        BroadcastHistoryView.as_view(),
        name="admin_broadcast_history",
    ),
    path(
        "notifications/history/<str:request_id>/resend/",
        BroadcastResendView.as_view(),
        name="admin_broadcast_resend",
    ),
    path(
        "notifications/broadcast/",
        GlobalNotificationView.as_view(),
        name="admin_broadcast",
    ),
    # User ViewSet
    path("users/", AdminUserViewSet.as_view({"get": "list"}), name="admin_user_list"),
    path(
        "users/export/",
        AdminUserViewSet.as_view({"get": "export"}),
        name="admin_user_export",
    ),
    path(
        "users/bulk/",
        AdminUserViewSet.as_view({"post": "bulk_action"}),
        name="admin_user_bulk",
    ),
    path(
        "users/<str:username>/details/",
        AdminUserViewSet.as_view({"get": "retrieve"}),
        name="admin_user_details",
    ),
    path(
        "users/<str:username>/role/",
        AdminUserViewSet.as_view({"patch": "update_role"}),
        name="admin_user_role",
    ),
    path(
        "users/<str:username>/notes/",
        AdminUserViewSet.as_view({"get": "notes", "post": "notes"}),
        name="admin_user_notes",
    ),
    path(
        "users/<str:username>/toggle-block/",
        AdminUserViewSet.as_view({"post": "toggle_block"}),
        name="admin_toggle_block_user",
    ),
    path(
        "users/<str:username>/delete/",
        AdminUserViewSet.as_view({"delete": "destroy"}),
        name="admin_delete_user",
    ),
    path(
        "system/integrity/",
        SystemIntegrityView.as_view(),
        name="admin_system_integrity",
    ),
    path("system/health/", SystemHealthView.as_view(), name="admin_system_health"),
    # Report ViewSet
    path(
        "reports/",
        AdminReportViewSet.as_view({"get": "list", "post": "create"}),
        name="admin_reports",
    ),
    path(
        "reports/<int:report_id>/",
        AdminReportViewSet.as_view({"patch": "partial_update"}),
        name="admin_report_detail",
    ),
    path(
        "store/items/<int:item_id>/duplicate/",
        StoreItemDuplicateView.as_view(),
        name="admin_store_item_duplicate",
    ),
]
