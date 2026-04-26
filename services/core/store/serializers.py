from rest_framework import serializers

from .models import StoreItem


class StoreItemSerializer(serializers.ModelSerializer):
    """Serializer for store items."""

    class Meta:
        model = StoreItem
        fields = [
            "id",
            "name",
            "description",
            "cost",
            "icon_name",
            "category",
            "image",
            "item_data",
            "featured",
            "is_active",
        ]


class PurchaseResponseSerializer(serializers.Serializer):
    """Serializer for successful purchase response."""

    status = serializers.CharField()
    message = serializers.CharField()
    remaining_xp = serializers.IntegerField()
    item = StoreItemSerializer()


class InventoryResponseSerializer(serializers.Serializer):
    """Serializer for user inventory and equipped items."""

    purchased_items = StoreItemSerializer(many=True)
    equipped_items = serializers.DictField()


class EquipItemRequestSerializer(serializers.Serializer):
    """Serializer for equipping an item."""

    item_id = serializers.IntegerField()


class UnequipItemRequestSerializer(serializers.Serializer):
    """Serializer for unequipping a category."""

    category = serializers.ChoiceField(choices=["THEME", "FONT", "EFFECT", "VICTORY"])
