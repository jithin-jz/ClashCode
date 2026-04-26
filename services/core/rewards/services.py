import logging

from django.utils import timezone
from xpoint.services import StreakService, XPService

from .models import DailyCheckIn

logger = logging.getLogger(__name__)


class RewardService:
    """
    Business logic for managing daily rewards and check-ins.
    """

    # XP rewards for each cycle day
    DAILY_REWARDS = {1: 5, 2: 10, 3: 15, 4: 20, 5: 25, 6: 30, 7: 35}

    @classmethod
    def get_check_in_status(cls, user):
        """Returns the current check-in status and cycle state for a user."""
        today = timezone.now().date()
        cycle_day, cycle_start_date, _ = StreakService.get_cycle_state(user)

        today_checkin = DailyCheckIn.objects.filter(user=user, check_in_date=today).first()

        current_cycle_checkins = DailyCheckIn.objects.filter(user=user, check_in_date__gte=cycle_start_date)

        return {
            "checked_in_today": today_checkin is not None,
            "current_streak": (cycle_day if today_checkin else (cycle_day - 1)),
            "cycle_day": cycle_day,
            "cycle_start_date": cycle_start_date,
            "today_checkin": today_checkin,
            "recent_checkins": current_cycle_checkins,
            "daily_rewards": cls.DAILY_REWARDS,
        }

    @classmethod
    def process_check_in(cls, user):
        """Processes a daily check-in for a user."""
        today = timezone.now().date()

        # 1. Check if already checked in
        existing = DailyCheckIn.objects.filter(user=user, check_in_date=today).first()
        if existing:
            raise ValueError("Already checked in today")

        # 2. Get cycle state
        cycle_day, cycle_start_date, is_reset = StreakService.get_cycle_state(user)
        xp_reward = cls.DAILY_REWARDS.get(cycle_day, 5)

        # 3. Create record
        checkin = DailyCheckIn.objects.create(user=user, streak_day=cycle_day, xp_earned=xp_reward)

        # 4. Award XP
        XPService.add_xp(user, xp_reward, source=XPService.SOURCE_CHECK_IN)

        return {
            "check_in": checkin,
            "xp_earned": xp_reward,
            "total_xp": user.profile.xp,
            "cycle_day": cycle_day,
            "is_new_cycle": is_reset,
            "cycle_start_date": cycle_start_date,
        }
