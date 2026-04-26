import logging

from challenges.models import UserProgress
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count, Q
from users.models import UserProfile

logger = logging.getLogger(__name__)


class LeaderboardService:
    """
    Service for calculating and caching user rankings.
    """

    CACHE_KEY = "leaderboard_data"
    CACHE_TIMEOUT = 60 * 10  # 10 minutes

    @staticmethod
    def get_leaderboard(limit: int = 100, use_cache: bool = True) -> list[dict]:
        """
        Retrieves the top users by XP and completed challenges.
        Uses cache by default for performance.
        """
        if use_cache:
            cached_data = cache.get(LeaderboardService.CACHE_KEY)
            if cached_data is not None:
                return cached_data

        data = LeaderboardService.build_leaderboard_data(limit)
        cache.set(LeaderboardService.CACHE_KEY, data, timeout=LeaderboardService.CACHE_TIMEOUT)
        return data

    @staticmethod
    def build_leaderboard_data(limit: int = 100) -> list[dict]:
        """
        Queries the database for user rankings.
        """
        User = get_user_model()
        users = (
            User.objects.annotate(
                completed_count=Count(
                    "challenge_progress",
                    filter=Q(
                        challenge_progress__status=UserProgress.Status.COMPLETED,
                    ),
                )
            )
            .select_related("profile")
            .filter(is_active=True, is_staff=False, is_superuser=False)
            .order_by("-profile__xp", "-completed_count", "id")[:limit]
        )

        data = []
        for user in users:
            avatar_url = None
            xp = 0
            try:
                profile = user.profile
                avatar_url = profile.avatar.url if profile.avatar else None
                xp = profile.xp
            except UserProfile.DoesNotExist:
                pass

            data.append(
                {
                    "username": user.username,
                    "avatar": avatar_url,
                    "completed_levels": user.completed_count,
                    "xp": xp,
                }
            )
        return data
