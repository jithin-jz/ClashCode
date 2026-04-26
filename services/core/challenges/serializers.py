from rest_framework import serializers

from .models import Challenge, UserProgress


class ChallengePublicSerializer(serializers.ModelSerializer):
    """Serializer for public challenge details, omitting sensitive fields."""

    class Meta:
        model = Challenge
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "initial_code",
            "order",
            "xp_reward",
            "time_limit",
            "target_time_seconds",
            "created_for_user",
        ]


class ChallengeAdminSerializer(serializers.ModelSerializer):
    """Full serializer for administrative CRUD operations."""

    created_for_user_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Challenge
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "initial_code",
            "test_code",
            "order",
            "xp_reward",
            "time_limit",
            "target_time_seconds",
            "created_for_user",
            "created_for_user_id",
        ]


class UserProgressSerializer(serializers.ModelSerializer):
    """Serializer for tracking user progress on a challenge."""

    challenge_id = serializers.IntegerField(source="challenge.id")

    class Meta:
        model = UserProgress
        fields = ["challenge_id", "status", "stars", "completed_at"]


# --- Request/Response Serializers for Challenge Actions ---


class ChallengeSubmissionRequestSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)


class ChallengeExecuteRequestSerializer(serializers.Serializer):
    code = serializers.CharField(required=False, allow_blank=True)


class AIAssistPurchaseResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    remaining_xp = serializers.IntegerField()
    hints_purchased = serializers.IntegerField()
    cost = serializers.IntegerField()
    message = serializers.CharField()


class AIHintRequestSerializer(serializers.Serializer):
    user_code = serializers.CharField(required=False, allow_blank=True)
    hint_level = serializers.IntegerField(min_value=1, max_value=3)


class AIAnalysisRequestSerializer(serializers.Serializer):
    user_code = serializers.CharField(required=False, allow_blank=True)


class AITaskStatusResponseSerializer(serializers.Serializer):
    task_id = serializers.CharField()
    status = serializers.CharField()
    result = serializers.JSONField(required=False)
    error = serializers.CharField(required=False)
    traceback = serializers.CharField(required=False)
    date_done = serializers.DateTimeField(allow_null=True, required=False)


class ChallengeContextResponseSerializer(serializers.Serializer):
    challenge_title = serializers.CharField()
    challenge_description = serializers.CharField()
    description = serializers.CharField()
    initial_code = serializers.CharField()
    test_code = serializers.CharField()


class LeaderboardEntrySerializer(serializers.Serializer):
    username = serializers.CharField()
    avatar = serializers.URLField(allow_null=True)
    completed_levels = serializers.IntegerField()
    xp = serializers.IntegerField()
