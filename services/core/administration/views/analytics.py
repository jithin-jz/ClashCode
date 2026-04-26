from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from administration.permissions import IsAdminUser
from administration.serializers import (
    AdminStatsSerializer,
    ChallengeAnalyticsSerializer,
    StoreAnalyticsSerializer,
    UltimateAnalyticsSerializer,
    UserEngagementAnalyticsSerializer,
)
from administration.services.analytics_service import AnalyticsService


class AdminStatsView(APIView):
    """View to get admin dashboard statistics."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        responses={200: AdminStatsSerializer, 403: OpenApiTypes.OBJECT},
        description="Get administration statistics including total users, active sessions, and economy totals.",
    )
    def get(self, request):
        data = AnalyticsService.get_admin_dashboard_stats(request=request)
        return Response(data, status=status.HTTP_200_OK)


class ChallengeAnalyticsView(APIView):
    """View to get detailed challenge performance analytics."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        responses={200: ChallengeAnalyticsSerializer(many=True)},
        description="Get detailed challenge performance analytics including completion rates and average stars.",
    )
    def get(self, request):
        results = AnalyticsService.get_challenge_analytics(request=request)
        return Response(results, status=status.HTTP_200_OK)


class StoreAnalyticsView(APIView):
    """View to get store economy and item popularity."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        responses={200: StoreAnalyticsSerializer},
        description="Get store economy analytics, item popularity, and total XP revenue.",
    )
    def get(self, request):
        data = AnalyticsService.get_store_analytics(request=request)
        return Response(data, status=status.HTTP_200_OK)


class UserEngagementAnalyticsView(APIView):
    """View to get user engagement and growth analytics."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        responses={200: UserEngagementAnalyticsSerializer},
        description="Get user growth trends, active session counts, and auth provider distribution.",
    )
    def get(self, request):
        data = AnalyticsService.get_user_engagement_analytics(request=request)
        return Response(data, status=status.HTTP_200_OK)


class UltimateAnalyticsView(APIView):
    """Unified command center view for all system analytics."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        responses={200: UltimateAnalyticsSerializer},
        description="Consolidated analytics including growth, economy, and performance leaderboards.",
    )
    def get(self, request):
        data = AnalyticsService.get_ultimate_analytics(request=request)
        return Response(data, status=status.HTTP_200_OK)
