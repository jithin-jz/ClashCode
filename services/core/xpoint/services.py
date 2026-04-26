import logging

from django.db import transaction
from django.utils import timezone
from users.models import UserProfile

from .models import XPTransaction

logger = logging.getLogger(__name__)


class XPService:
    SOURCE_CHECK_IN = "check_in"
    SOURCE_PURCHASE = "purchase"
    SOURCE_REFERRAL = "referral"
    SOURCE_CHALLENGE = "challenge"
    SOURCE_ADMIN = "admin"

    @staticmethod
    def add_xp(user, amount, source=None, description=None):
        """Add XP to a user's profile and record the transaction."""
        if amount == 0:
            return user.profile.xp

        try:
            with transaction.atomic():
                profile = UserProfile.objects.select_for_update().get(user=user)

                new_total = profile.xp + amount
                if new_total < 0:
                    raise ValueError("Insufficient XP")

                profile.xp = new_total
                profile.save()

                # Record transaction
                XPTransaction.objects.create(
                    user=user,
                    amount=amount,
                    balance_after=new_total,
                    source=source or XPService.SOURCE_ADMIN,
                    description=description,
                )

                logger.info(f"XP_TX: {user.username} {amount:+} XP ({source}). New: {profile.xp}")

                return profile.xp

        except UserProfile.DoesNotExist:
            logger.error(f"UserProfile not found for user {user.username}")
            raise
        except Exception as e:
            logger.error(f"Failed to add XP to user {user.username}: {str(e)}")
            raise

    @staticmethod
    def get_user_xp(user):
        """Get the current XP of a user."""
        return user.profile.xp


class StreakService:
    """
    Service layer for handling Reward Cycle logic.

    This service determines the current day in the 7-day reward cycle.
    Logic:
    1. Cycle starts on the first check-in (Day 1).
    2. It continues for 7 days regardless of check-ins.
    3. If a day is missed, it's skipped (cannot be claimed).
    4. After 7 days, the cycle resets to Day 1.
    """

    @staticmethod
    def get_cycle_state(user):
        """
        Determines the current cycle day and handles resets.
        Returns: (current_day_index, cycle_start_date, is_reset)
        """
        today = timezone.now().date()
        profile = user.profile

        # Case 1: New user or first time using system
        if not profile.reward_cycle_start_date:
            profile.reward_cycle_start_date = today
            profile.save()
            return 1, today, True

        days_elapsed = (today - profile.reward_cycle_start_date).days

        # Case 2: Cycle completed (7 days passed, so day index > 7)
        # 0-indexed difference. Day 1 is diff 0. Day 7 is diff 6.
        # If diff is 7, it's the 8th day -> Reset.
        if days_elapsed >= 7:
            profile.reward_cycle_start_date = today
            profile.save()
            return 1, today, True

        # Case 3: Within valid cycle
        cycle_day = days_elapsed + 1
        return cycle_day, profile.reward_cycle_start_date, False
