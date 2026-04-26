from django.core.cache import cache
from django.db import connection
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring service status.
    Checks database, cache, and Redis connectivity.
    """

    permission_classes = []  # Public endpoint

    @extend_schema(
        responses={
            200: OpenApiTypes.OBJECT,
            503: OpenApiTypes.OBJECT,
        },
        description="Check the health of the core service (DB, Cache, Redis).",
    )
    def get(self, request):
        health_status = {"status": "healthy", "service": "core", "checks": {}}

        # Check database
        try:
            connection.ensure_connection()
            health_status["checks"]["database"] = "ok"
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["checks"]["database"] = f"error: {str(e)}"

        # Check cache (Redis)
        try:
            cache.set("health_check", "ok", 10)
            cache_value = cache.get("health_check")
            if cache_value == "ok":
                health_status["checks"]["cache"] = "ok"
            else:
                health_status["status"] = "unhealthy"
                health_status["checks"]["cache"] = "error: cache read/write failed"
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["checks"]["cache"] = f"error: {str(e)}"

        # Determine HTTP status code
        status_code = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(health_status, status=status_code)
