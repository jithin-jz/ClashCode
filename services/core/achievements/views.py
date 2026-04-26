from rest_framework import generics, permissions

from .serializers import AchievementSerializer, UserAchievementSerializer
from .services import AchievementService


class AchievementListView(generics.ListAPIView):
    """List all achievements with unlock status for the current user."""

    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AchievementService.get_user_visible_achievements(self.request.user)


class UserAchievementListView(generics.ListAPIView):
    """List achievements unlocked by a specific user (for profile display)."""

    serializer_class = UserAchievementSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        username = self.kwargs.get("username")
        return AchievementService.get_user_unlocked_achievements(username)
