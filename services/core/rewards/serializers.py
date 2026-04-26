from rest_framework import serializers

from .models import DailyCheckIn


class DailyCheckInSerializer(serializers.ModelSerializer):
    """Serializer for individual check-in records."""

    class Meta:
        model = DailyCheckIn
        fields = ["id", "check_in_date", "streak_day", "xp_earned", "created_at"]
        read_only_fields = [
            "id",
            "check_in_date",
            "streak_day",
            "xp_earned",
            "created_at",
        ]


class CheckInSuccessSerializer(serializers.Serializer):
    """Serializer for a successful check-in response."""

    message = serializers.CharField()
    check_in = DailyCheckInSerializer()
    xp_earned = serializers.IntegerField()
    total_xp = serializers.IntegerField()
    cycle_day = serializers.IntegerField()
    is_new_cycle = serializers.BooleanField()
    cycle_start_date = serializers.DateField()


class CheckInStatusSerializer(serializers.Serializer):
    """Serializer for the check-in status response."""

    checked_in_today = serializers.BooleanField()
    current_streak = serializers.IntegerField()
    cycle_day = serializers.IntegerField()
    cycle_start_date = serializers.DateField()
    today_checkin = DailyCheckInSerializer(allow_null=True)
    recent_checkins = DailyCheckInSerializer(many=True)
    daily_rewards = serializers.DictField(child=serializers.IntegerField())
