import logging
import random

from challenges.models import UserProgress
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    inline_serializer,
)
from project.media import build_media_url
from rest_framework import parsers, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    FollowToggleResponseSerializer,
    PublicUserSerializer,
    RedeemReferralSerializer,
    UserSerializer,
    UserSummarySerializer,
)
from .services import UserService

logger = logging.getLogger(__name__)


def _set_auth_cookies(response, access_token: str, refresh_token: str | None = None):
    response.set_cookie(
        settings.JWT_ACCESS_COOKIE_NAME,
        access_token,
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        max_age=settings.JWT_ACCESS_TOKEN_LIFETIME,
        path="/",
    )
    if refresh_token:
        response.set_cookie(
            settings.JWT_REFRESH_COOKIE_NAME,
            refresh_token,
            httponly=True,
            secure=settings.JWT_COOKIE_SECURE,
            samesite=settings.JWT_COOKIE_SAMESITE,
            max_age=settings.JWT_REFRESH_TOKEN_LIFETIME,
            path="/",
        )


@method_decorator(never_cache, name="dispatch")
class CurrentUserView(APIView):
    """Get the currently authenticated user."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request):
        user_data = UserSerializer(request.user, context={"request": request}).data

        if getattr(settings, "JWT_RETURN_TOKENS_IN_BODY", False):
            user_data["access_token"] = request.COOKIES.get(settings.JWT_ACCESS_COOKIE_NAME)
            user_data["refresh_token"] = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)

        return Response(user_data, status=status.HTTP_200_OK)


class ProfileUpdateView(APIView):
    """Updates the authenticated user's profile information."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @extend_schema(
        request=UserSerializer,
        responses={200: UserSerializer},
        description="Update current user profile and identity details.",
    )
    def patch(self, request):
        try:
            user = UserService.update_profile(request.user, request.data, request.FILES)

            # Generate new tokens to reflect updated claims (username/avatar)
            from authentication.utils import generate_tokens

            tokens = generate_tokens(user)

            data = UserSerializer(user, context={"request": request}).data
            if getattr(settings, "JWT_RETURN_TOKENS_IN_BODY", False):
                data["access_token"] = tokens["access_token"]
                data["refresh_token"] = tokens["refresh_token"]

            response = Response(data, status=status.HTTP_200_OK)
            _set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
            return response

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProfileDetailView(APIView):
    """View to get public profile details."""

    permission_classes = [AllowAny]
    serializer_class = PublicUserSerializer

    @extend_schema(
        parameters=[OpenApiParameter("username", str, OpenApiParameter.PATH)],
        responses={200: PublicUserSerializer, 404: OpenApiTypes.OBJECT},
        description="Get public profile details by username.",
    )
    def get(self, request, username):
        profile_data = UserService.get_public_profile(username, viewer=request.user)
        if not profile_data:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(profile_data, status=status.HTTP_200_OK)


class FollowToggleView(APIView):
    """View to toggle follow status."""

    permission_classes = [IsAuthenticated]
    serializer_class = FollowToggleResponseSerializer

    @extend_schema(
        parameters=[OpenApiParameter("username", str, OpenApiParameter.PATH)],
        responses={
            200: FollowToggleResponseSerializer,
            201: FollowToggleResponseSerializer,
            404: OpenApiTypes.OBJECT,
        },
        description="Toggle follow/unfollow for a user.",
    )
    def post(self, request, username):
        try:
            is_following, followers, following = UserService.toggle_follow(request.user, username)

            return Response(
                {
                    "is_following": is_following,
                    "follower_count": followers,
                    "following_count": following,
                },
                status=status.HTTP_201_CREATED if is_following else status.HTTP_200_OK,
            )

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=(status.HTTP_400_BAD_REQUEST if "yourself" in str(e) else status.HTTP_404_NOT_FOUND),
            )


class UserFollowersView(APIView):
    """View to get list of followers for a user."""

    permission_classes = [AllowAny]
    serializer_class = UserSummarySerializer

    def get(self, request, username):
        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        followers = target_user.followers.select_related("follower", "follower__profile")
        # Optimization: serialize list using serializer
        # We need to adapt the structure slightly if needed, but UserSummarySerializer should work
        # However, the source is a list of UserFollow objects, so we need to extract followers
        follower_users = [rel.follower for rel in followers]
        serializer = UserSummarySerializer(follower_users, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserFollowingView(APIView):
    """View to get list of users a user is following."""

    permission_classes = [AllowAny]
    serializer_class = UserSummarySerializer

    def get(self, request, username):
        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        following = target_user.following.select_related("following", "following__profile")
        following_users = [rel.following for rel in following]
        serializer = UserSummarySerializer(following_users, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class RedeemReferralView(APIView):
    """View to redeem a referral code."""

    permission_classes = [IsAuthenticated]
    serializer_class = RedeemReferralSerializer

    @extend_schema(
        request=RedeemReferralSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        description="Redeem a referral code to earn XP.",
    )
    def post(self, request):
        code = (request.data.get("code") or "").strip()
        try:
            result = UserService.redeem_referral(request.user, code)
            return Response(
                {
                    "message": "Referral code redeemed successfully",
                    "xp_awarded": 100,
                    "new_total_xp": result["new_total_xp"],
                    "referrer_new_total_xp": result["referrer_new_total_xp"],
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SuggestedUsersView(APIView):
    """View to get suggested users to follow."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserSummarySerializer

    def get(self, request):
        following_ids = request.user.following.values_list("following_id", flat=True)
        candidate_ids = list(
            User.objects.exclude(id__in=list(following_ids) + [request.user.id])
            .exclude(is_superuser=True)
            .exclude(is_staff=True)
            .order_by("-date_joined", "-id")
            .values_list("id", flat=True)[:500]
        )

        if len(candidate_ids) > 50:
            candidate_ids = random.sample(candidate_ids, 50)

        suggested = User.objects.filter(id__in=candidate_ids).select_related("profile")
        serializer = UserSummarySerializer(suggested, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ContributionHistoryView(APIView):
    """View to get contribution history for the contribution graph."""

    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[OpenApiParameter("username", str, OpenApiParameter.PATH)],
        responses={
            200: inline_serializer(
                name="ContributionHistoryResponse",
                fields={
                    "date": serializers.DateField(),
                    "count": serializers.IntegerField(),
                },
                many=True,
            ),
            404: OpenApiTypes.OBJECT,
        },
        description="Retrieve a map of daily contributions (completed challenges) for the last 365 days.",
    )
    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        contributions = (
            UserProgress.objects.filter(
                user=user,
                status=UserProgress.Status.COMPLETED,
                completed_at__isnull=False,
            )
            .annotate(date=TruncDate("completed_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("-date")[:365]
        )

        formatted_data = [
            {"date": row["date"].isoformat(), "count": row["count"]}
            for row in contributions
            if row["date"] is not None
        ]

        return Response(formatted_data, status=status.HTTP_200_OK)
