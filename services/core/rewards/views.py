from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    CheckInStatusSerializer,
    CheckInSuccessSerializer,
    DailyCheckInSerializer,
)
from .services import RewardService


class CheckInView(APIView):
    """
    API View to handle daily user check-ins and reward distribution.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = DailyCheckInSerializer

    @extend_schema(
        request=None,
        responses={
            201: CheckInSuccessSerializer,
            400: OpenApiTypes.OBJECT,
        },
        description="Process a daily check-in and award XP based on the current streak.",
    )
    def post(self, request):
        """Action to perform a daily check-in."""
        try:
            result = RewardService.process_check_in(request.user)

            response_data = {
                "message": f"Check-in successful! Day {result['cycle_day']} of cycle.",
                **result,
            }
            # For frontend compatibility, ensure streak_day is present
            response_data["streak_day"] = result["cycle_day"]

            serializer = CheckInSuccessSerializer(response_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            # Re-fetch status to provide existing check-in data on error
            status_data = RewardService.get_check_in_status(request.user)
            return Response(
                {
                    "error": str(e),
                    "check_in": (
                        DailyCheckInSerializer(status_data["today_checkin"]).data
                        if status_data["today_checkin"]
                        else None
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        responses={200: CheckInStatusSerializer},
        description="Retrieve the user's current check-in status and cycle history.",
    )
    def get(self, request):
        """Action to get check-in status."""
        status_data = RewardService.get_check_in_status(request.user)
        serializer = CheckInStatusSerializer(status_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
