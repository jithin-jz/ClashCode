from django.contrib.auth.models import User
from drf_spectacular.utils import OpenApiTypes, extend_schema_field
from project.media import build_file_url
from rest_framework import serializers

from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    # Computed field to indicate whether this user was referred by someone
    is_referred = serializers.SerializerMethodField()

    # Map ImageFields to URLs for frontend compatibility
    avatar_url = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile

        # Only expose non-sensitive, UI-relevant profile fields
        # Tokens, provider_id, referred_by are intentionally excluded
        fields = [
            "provider",
            "avatar_url",
            "banner_url",
            "bio",
            "xp",
            "referral_code",
            "is_referred",
            "created_at",
            "streak_freezes",
            "active_theme",
            "active_font",
            "active_effect",
            "active_victory",
        ]

    @extend_schema_field(bool)
    def get_is_referred(self, obj):
        # Boolean derived from presence of a referrer
        return obj.referred_by is not None

    @extend_schema_field(OpenApiTypes.URI)
    def get_avatar_url(self, obj):
        return build_file_url(obj.avatar, self.context.get("request"))

    @extend_schema_field(OpenApiTypes.URI)
    def get_banner_url(self, obj):
        return build_file_url(obj.banner, self.context.get("request"))


class UserSerializer(serializers.ModelSerializer):
    # Profile is injected manually to avoid nested serializer overhead
    profile = serializers.SerializerMethodField()

    # Social graph metrics (computed, not stored)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User

        # Includes permission flags for admin-aware frontends
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "profile",  # Nested profile data (avatar, bio, etc.)
            "followers_count",  # Social proof metric
            "following_count",  # Social proof metric
            "is_staff",  # For Access Control (e.g. show Admin Link)
            "is_superuser",  # For Access Control
            "is_active",  # Status check
        ]

    @extend_schema_field(UserProfileSerializer)
    def get_profile(self, obj):
        # Defensive access in case profile was not created (edge cases)
        try:
            return UserProfileSerializer(obj.profile, context=self.context).data
        except Exception:
            return None

    @extend_schema_field(int)
    def get_followers_count(self, obj):
        # Count of users following this user
        if hasattr(obj, "followers_total"):
            return obj.followers_total
        return obj.followers.count()

    @extend_schema_field(int)
    def get_following_count(self, obj):
        # Count of users this user follows
        if hasattr(obj, "following_total"):
            return obj.following_total
        return obj.following.count()


class UserSummarySerializer(serializers.Serializer):
    username = serializers.CharField()
    avatar_url = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.URI)
    def get_avatar_url(self, obj):
        if not hasattr(obj, "profile"):
            return None
        return build_file_url(obj.profile.avatar, self.context.get("request"))

    @extend_schema_field(bool)
    def get_is_following(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            # Check if request.user is following obj (the user in the summary)
            return request.user.following.filter(following=obj).exists()
        return False

    @extend_schema_field(str)
    def get_bio(self, obj):
        return obj.profile.bio if hasattr(obj, "profile") else ""


class FollowToggleResponseSerializer(serializers.Serializer):
    is_following = serializers.BooleanField()
    follower_count = serializers.IntegerField()
    following_count = serializers.IntegerField()


class RedeemReferralSerializer(serializers.Serializer):
    code = serializers.CharField(required=True, help_text="The referral code to redeem.")


class PublicUserProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "avatar_url",
            "banner_url",
            "bio",
            "xp",
            "created_at",
            "active_theme",
            "active_font",
            "active_effect",
            "active_victory",
        ]

    @extend_schema_field(OpenApiTypes.URI)
    def get_avatar_url(self, obj):
        return build_file_url(obj.avatar, self.context.get("request"))

    @extend_schema_field(OpenApiTypes.URI)
    def get_banner_url(self, obj):
        return build_file_url(obj.banner, self.context.get("request"))


class PublicUserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "profile",
            "followers_count",
            "following_count",
        ]

    @extend_schema_field(PublicUserProfileSerializer)
    def get_profile(self, obj):
        try:
            return PublicUserProfileSerializer(obj.profile, context=self.context).data
        except Exception:
            return None

    @extend_schema_field(int)
    def get_followers_count(self, obj):
        if hasattr(obj, "followers_total"):
            return obj.followers_total
        return obj.followers.count()

    @extend_schema_field(int)
    def get_following_count(self, obj):
        if hasattr(obj, "following_total"):
            return obj.following_total
        return obj.following.count()
