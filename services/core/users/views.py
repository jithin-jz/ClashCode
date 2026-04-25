import random

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db import transaction, IntegrityError
from django.db.models import Case, Count, IntegerField, When
from django.db.models.functions import TruncDate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import (
    extend_schema,
    OpenApiTypes,
    inline_serializer,
    OpenApiParameter,
)
from rest_framework import serializers
from .models import UserProfile, UserFollow

from .serializers import (
    UserSerializer,
    PublicUserSerializer,
    UserSummarySerializer,
    FollowToggleResponseSerializer,
    RedeemReferralSerializer,
)


from xpoint.services import XPService
from challenges.models import UserProgress


from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from project.media import build_file_url


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
            # Extract tokens from the request if possible
            access_token = request.COOKIES.get(settings.JWT_ACCESS_COOKIE_NAME)
            if not access_token:
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    access_token = auth_header.split(" ")[1]
            
            refresh_token = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
            
            if access_token:
                user_data["access_token"] = access_token
            if refresh_token:
                user_data["refresh_token"] = refresh_token
                
        return Response(user_data, status=status.HTTP_200_OK)


class ProfileUpdateView(APIView):
    """
    Updates the authenticated user's profile information.

    This view handles patches to both the core `User` model and the `UserProfile` model.

    **Supported Updates:**
    - **Identity**: `username`, `first_name`, `last_name`
    - **Profile**: `bio`
    - **Media**: `avatar`, `banner` (File uploads)

    Returns the updated user object.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @extend_schema(
        request=UserSerializer,
        responses={200: UserSerializer},
        description="Update current user profile and identity details.",
    )
    def patch(self, request):
        user = request.user
        data = request.data
        old_username = user.username
        username_validator = UnicodeUsernameValidator()

        # 1. Validate username first so we can return clean API errors.
        if "username" in data:
            requested_username = str(data.get("username", "")).strip()
            if not requested_username:
                return Response(
                    {"error": "Username cannot be empty."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                username_validator(requested_username)
            except ValidationError:
                return Response(
                    {
                        "error": "Username can only contain letters, numbers, and @/./+/-/_ characters."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            username_taken = (
                User.objects.filter(username__iexact=requested_username)
                .exclude(pk=user.pk)
                .exists()
            )
            if username_taken:
                return Response(
                    {"error": "Username is already taken."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.username = requested_username

        if "first_name" in data:
            user.first_name = str(data.get("first_name", "")).strip()
        if "last_name" in data:
            user.last_name = str(data.get("last_name", "")).strip()

        profile = user.profile
        if "bio" in data:
            profile.bio = str(data.get("bio", ""))

        if "avatar" in request.FILES:
            profile.avatar = request.FILES["avatar"]

        if "banner" in request.FILES:
            profile.banner = request.FILES["banner"]

        try:
            with transaction.atomic():
                user.save()
                profile.save()
        except IntegrityError:
            return Response(
                {"error": "Username is already taken."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Invalidate profile cache
        cache.delete(f"profile:{old_username}")
        cache.delete(f"profile:{user.username}")

        # Generate new tokens to reflect updated claims (username/avatar)
        from auth.utils import generate_tokens

        tokens = generate_tokens(user)

        data = UserSerializer(user, context={"request": request}).data
        if getattr(settings, "JWT_RETURN_TOKENS_IN_BODY", False):
            data["access_token"] = tokens["access_token"]
            data["refresh_token"] = tokens["refresh_token"]

        response = Response(data, status=status.HTTP_200_OK)
        _set_auth_cookies(
            response,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
        )
        return response


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
        # Try to get from cache first
        cache_key = f"profile:{username}"
        data = cache.get(cache_key)

        if not data:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )

            data = PublicUserSerializer(user, context={"request": request}).data

            # Add stats (redundant if serializer has them, but ensuring consistency)
            data["followers_count"] = user.followers.count()
            data["following_count"] = user.following.count()

            # Cache the public data for 5 minutes
            cache.set(cache_key, data, 300)
        else:
            # Avoid mutating cached objects with request-specific flags.
            data = dict(data)

        # Inject request-specific data (NEVER CACHE THIS)
        if request.user.is_authenticated:
            # Check if relationship exists.
            # We use the relationship model directly to avoid fetching the user object if data came from cache
            data["is_following"] = UserFollow.objects.filter(
                follower=request.user, following__username=username
            ).exists()
        else:
            data["is_following"] = False

        return Response(data, status=status.HTTP_200_OK)


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
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if target_user == request.user:
            return Response(
                {"error": "Cannot follow yourself"}, status=status.HTTP_400_BAD_REQUEST
            )

        follow, created = UserFollow.objects.get_or_create(
            follower=request.user, following=target_user
        )

        if not created:
            # If relationship exists, unfollow
            follow.delete()
            is_following = False
        else:
            is_following = True

        # Invalidate profile cache because followers_count changed
        cache.delete(f"profile:{username}")

        return_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            {
                "is_following": is_following,
                "follower_count": target_user.followers.count(),
                "following_count": target_user.following.count(),
            },
            status=return_status,
        )


class UserFollowersView(APIView):
    """View to get list of followers for a user."""

    permission_classes = [AllowAny]
    serializer_class = UserSummarySerializer

    def get(self, request, username):
        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        followers = target_user.followers.select_related(
            "follower", "follower__profile"
        )
        following_ids = set()
        if request.user.is_authenticated:
            following_ids = set(
                request.user.following.values_list("following_id", flat=True)
            )

        data = []

        for rel in followers:
            follower_user = rel.follower
            profile = getattr(follower_user, "profile", None)

            data.append(
                {
                    "username": follower_user.username,
                    "first_name": follower_user.first_name,
                    "avatar_url": (
                        build_file_url(profile.avatar, request) if profile else None
                    ),
                    "is_following": follower_user.id in following_ids,
                }
            )

        return Response(data, status=status.HTTP_200_OK)


class UserFollowingView(APIView):
    """View to get list of users a user is following."""

    permission_classes = [AllowAny]
    serializer_class = UserSummarySerializer

    def get(self, request, username):
        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        following = target_user.following.select_related(
            "following", "following__profile"
        )
        following_ids = set()
        if request.user.is_authenticated:
            following_ids = set(
                request.user.following.values_list("following_id", flat=True)
            )

        data = []

        for rel in following:
            following_user = rel.following
            profile = getattr(following_user, "profile", None)

            data.append(
                {
                    "username": following_user.username,
                    "first_name": following_user.first_name,
                    "avatar_url": (
                        build_file_url(profile.avatar, request) if profile else None
                    ),
                    "is_following": following_user.id in following_ids,
                }
            )

        return Response(data, status=status.HTTP_200_OK)


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

        code = (request.data.get("code") or "").strip().upper()

        if not code:
            return Response(
                {"error": "Referral code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            try:
                profile = UserProfile.objects.select_for_update().get(user=request.user)
            except UserProfile.DoesNotExist:
                return Response(
                    {"error": "User profile not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if profile.referred_by:
                return Response(
                    {"error": "You have already redeemed a referral code"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if profile.referral_code == code:
                return Response(
                    {"error": "Cannot redeem your own referral code"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                referrer_profile = UserProfile.objects.select_related("user").get(
                    referral_code=code
                )
            except UserProfile.DoesNotExist:
                return Response(
                    {"error": "Invalid referral code"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            profile.referred_by = referrer_profile.user
            profile.save(update_fields=["referred_by", "updated_at"])

            new_total_xp = XPService.add_xp(
                request.user, 100, source=XPService.SOURCE_REFERRAL
            )
            referrer_new_total_xp = XPService.add_xp(
                referrer_profile.user, 100, source=XPService.SOURCE_REFERRAL
            )

            # Profile detail is cached; invalidate both users so XP updates are visible immediately.
            cache.delete(f"profile:{request.user.username}")
            cache.delete(f"profile:{referrer_profile.user.username}")

        return Response(
            {
                "message": "Referral code redeemed successfully",
                "xp_awarded": 100,
                "redeemer_xp_awarded": 100,
                "referrer_xp_awarded": 100,
                "new_total_xp": new_total_xp,
                "referrer_new_total_xp": referrer_new_total_xp,
            },
            status=status.HTTP_200_OK,
        )


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
        if not candidate_ids:
            return Response([], status=status.HTTP_200_OK)

        ordering = Case(
            *[
                When(id=user_id, then=position)
                for position, user_id in enumerate(candidate_ids)
            ],
            output_field=IntegerField(),
        )
        suggested = (
            User.objects.filter(id__in=candidate_ids)
            .select_related("profile")
            .order_by(ordering)
        )

        data = []
        for user in suggested:
            profile = getattr(user, "profile", None)
            data.append(
                {
                    "username": user.username,
                    "first_name": user.first_name,
                    "avatar_url": (
                        build_file_url(profile.avatar, request)
                        if profile and profile.avatar
                        else None
                    ),
                }
            )

        return Response(data, status=status.HTTP_200_OK)


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
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Build a daily contribution map from completed challenges in Postgres.
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
