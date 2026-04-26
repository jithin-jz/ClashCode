import logging

from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from xpoint.services import XPService

from .models import UserFollow, UserProfile

logger = logging.getLogger(__name__)


class UserService:
    """
    Service layer for user management, profiles, and social relationships.
    """

    @staticmethod
    def update_profile(user, data, files):
        """
        Updates user identity and profile details.
        """
        old_username = user.username
        username_validator = UnicodeUsernameValidator()
        profile = user.profile

        with transaction.atomic():
            # Handle username update
            if "username" in data:
                requested_username = str(data.get("username", "")).strip()
                if not requested_username:
                    raise ValueError("Username cannot be empty.")

                try:
                    username_validator(requested_username)
                except ValidationError:
                    raise ValueError("Username can only contain letters, numbers, and @/./+/-/_ characters.")

                if User.objects.filter(username__iexact=requested_username).exclude(pk=user.pk).exists():
                    raise ValueError("Username is already taken.")

                user.username = requested_username

            # Handle other User fields
            if "first_name" in data:
                user.first_name = str(data.get("first_name", "")).strip()
            if "last_name" in data:
                user.last_name = str(data.get("last_name", "")).strip()

            # Handle Profile fields
            if "bio" in data:
                profile.bio = str(data.get("bio", ""))

            if "avatar" in files:
                profile.avatar = files["avatar"]
            if "banner" in files:
                profile.banner = files["banner"]

            user.save()
            profile.save()

        # Cache Invalidation
        cache.delete(f"profile:{old_username}")
        cache.delete(f"profile:{user.username}")

        return user

    @staticmethod
    def toggle_follow(follower, target_username):
        """
        Toggles follow/unfollow relationship between two users.
        """
        try:
            target_user = User.objects.get(username=target_username)
        except User.DoesNotExist:
            raise ValueError("User not found")

        if target_user == follower:
            raise ValueError("Cannot follow yourself")

        follow, created = UserFollow.objects.get_or_create(follower=follower, following=target_user)

        if not created:
            follow.delete()
            is_following = False
        else:
            is_following = True

        # Invalidate cache
        cache.delete(f"profile:{target_username}")

        return (
            is_following,
            target_user.followers.count(),
            target_user.following.count(),
        )

    @staticmethod
    def redeem_referral(user, code):
        """
        Redeems a referral code for both redeemer and referrer.
        """
        code = (code or "").strip().upper()
        if not code:
            raise ValueError("Referral code is required")

        with transaction.atomic():
            profile = UserProfile.objects.select_for_update().get(user=user)

            if profile.referred_by:
                raise ValueError("You have already redeemed a referral code")

            if profile.referral_code == code:
                raise ValueError("Cannot redeem your own referral code")

            try:
                referrer_profile = UserProfile.objects.select_related("user").get(referral_code=code)
            except UserProfile.DoesNotExist:
                raise ValueError("Invalid referral code")

            profile.referred_by = referrer_profile.user
            profile.save(update_fields=["referred_by", "updated_at"])

            # Award XP
            new_total_xp = XPService.add_xp(user, 100, source=XPService.SOURCE_REFERRAL)
            referrer_new_total_xp = XPService.add_xp(referrer_profile.user, 100, source=XPService.SOURCE_REFERRAL)

            # Invalidate caches
            cache.delete(f"profile:{user.username}")
            cache.delete(f"profile:{referrer_profile.user.username}")

        return {
            "new_total_xp": new_total_xp,
            "referrer_new_total_xp": referrer_new_total_xp,
            "referrer_username": referrer_profile.user.username,
        }

    @staticmethod
    def get_public_profile(username, viewer=None):
        """
        Retrieves public profile with viewer-specific state (is_following).
        """
        cache_key = f"profile:{username}"
        data = cache.get(cache_key)

        if not data:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None

            from .serializers import PublicUserSerializer

            # Note: We pass None to context here because we want to cache general data
            data = PublicUserSerializer(user).data
            cache.set(cache_key, data, 300)
        else:
            data = dict(data)

        # Inject viewer-specific flags (Non-cacheable)
        if viewer and viewer.is_authenticated:
            data["is_following"] = UserFollow.objects.filter(follower=viewer, following__username=username).exists()
        else:
            data["is_following"] = False

        return data
