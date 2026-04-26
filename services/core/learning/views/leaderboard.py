from challenges.serializers import LeaderboardEntrySerializer
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..services import LeaderboardService


class LeaderboardView(generics.GenericAPIView):
    """
    View to retrieve the global user leaderboard.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = LeaderboardEntrySerializer

    @extend_schema(
        responses={200: LeaderboardEntrySerializer(many=True)},
        description="Get global leaderboard data (limited to top 100 users, cached and refreshed by the backend worker).",
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves the leaderboard data from the service (handles caching internally).
        """
        data = LeaderboardService.get_leaderboard()
        return Response(data, status=status.HTTP_200_OK)
