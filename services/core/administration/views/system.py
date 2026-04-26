from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from administration.permissions import IsAdminUser
from administration.serializers import SystemIntegritySerializer
from administration.services.system_service import SystemService


class SystemIntegrityView(APIView):
    """View to check core system health and counts."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        responses={200: SystemIntegritySerializer},
        description="Get current collection counts for key system models.",
    )
    def get(self, request):
        data = SystemService.get_system_integrity()
        serializer = SystemIntegritySerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SystemHealthView(APIView):
    """View to get operational health data."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Get lightweight operational health data for the admin dashboard.",
    )
    def get(self, request):
        data = SystemService.get_system_health()
        return Response(data, status=status.HTTP_200_OK)
