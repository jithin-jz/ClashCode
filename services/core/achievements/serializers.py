from rest_framework import serializers

from .models import Achievement, UserAchievement, UserAchievementProgress


class AchievementSerializer(serializers.ModelSerializer):
    """
    Standard achievement serializer.
    Includes progress tracking and unlock status.
    """

    is_unlocked = serializers.SerializerMethodField()
    unlocked_at = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Achievement
        fields = [
            "id",
            "slug",
            "title",
            "description",
            "icon",
            "category",
            "xp_reward",
            "target_value",
            "is_secret",
            "is_unlocked",
            "unlocked_at",
            "progress",
        ]

    def get_is_unlocked(self, obj):
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return False

        if "user_achievement" in self.context:
            return True

        return UserAchievement.objects.filter(user=request.user, achievement=obj).exists()

    def get_unlocked_at(self, obj):
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return None

        if "unlocked_at" in self.context:
            return self.context["unlocked_at"]

        ua = UserAchievement.objects.filter(user=request.user, achievement=obj).first()
        return ua.unlocked_at if ua else None

    def get_progress(self, obj):
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return None

        progress = UserAchievementProgress.objects.filter(user=request.user, achievement=obj).first()

        if not progress:
            return {"current": 0, "target": obj.target_value, "percentage": 0}

        return {
            "current": progress.current_value,
            "target": obj.target_value,
            "percentage": progress.percentage,
        }


class UserAchievementSerializer(serializers.ModelSerializer):
    """
    Serializer for achievements a user HAS unlocked.
    """

    achievement = serializers.SerializerMethodField()

    class Meta:
        model = UserAchievement
        fields = ["id", "achievement", "unlocked_at"]

    def get_achievement(self, obj):
        context = self.context.copy()
        context["user_achievement"] = True
        context["unlocked_at"] = obj.unlocked_at
        return AchievementSerializer(obj.achievement, context=context).data
