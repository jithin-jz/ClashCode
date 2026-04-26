from rest_framework import serializers

from .models import XPTransaction


class XPTransactionSerializer(serializers.ModelSerializer):
    """Serializer for XP transaction records."""

    source_display = serializers.CharField(source="get_source_display", read_only=True)

    class Meta:
        model = XPTransaction
        fields = [
            "id",
            "amount",
            "balance_after",
            "source",
            "source_display",
            "description",
            "created_at",
        ]
        read_only_fields = fields


class XPStatsSerializer(serializers.Serializer):
    """Serializer for user XP overview."""

    current_xp = serializers.IntegerField()
    total_earned = serializers.IntegerField()
    total_spent = serializers.IntegerField()
    transaction_count = serializers.IntegerField()
