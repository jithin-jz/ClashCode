import logging
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from xpoint.services import XPService

from .models import Purchase, StoreItem

logger = logging.getLogger(__name__)


class StoreService:
    """
    Business logic for managing store items, purchases, and inventory.
    """

    @staticmethod
    def purchase_item(user, item_id):
        """
        Handles the purchase of a store item using XP.
        """
        from django.shortcuts import get_object_or_404

        item = get_object_or_404(StoreItem, pk=item_id, is_active=True)

        if Purchase.objects.filter(user=user, item=item).exists():
            raise ValueError("You already own this item.")

        with transaction.atomic():
            try:
                remaining_xp = XPService.add_xp(
                    user,
                    -item.cost,
                    source="store_purchase",
                    description=f"Purchased {item.name}",
                )
            except ValueError:
                user.profile.refresh_from_db()
                shortage = max(0, item.cost - user.profile.xp)
                raise ValueError(f"Insufficient XP. Need {shortage} more.")

            Purchase.objects.create(user=user, item=item)

        return item, remaining_xp

    @staticmethod
    def equip_item(user, item_id):
        """
        Equips a purchased cosmetic item.
        """
        from django.shortcuts import get_object_or_404

        item = get_object_or_404(StoreItem, pk=item_id, is_active=True)

        if not Purchase.objects.filter(user=user, item=item).exists():
            raise PermissionError("You do not own this item.")

        profile = user.profile
        category = item.category
        item_data = item.item_data

        if category == "THEME":
            key = item_data.get("theme_key")
            if not key:
                raise ValueError("Invalid theme data.")
            profile.active_theme = key
        elif category == "FONT":
            key = item_data.get("font_family")
            if not key:
                raise ValueError("Invalid font data.")
            profile.active_font = key
        elif category == "EFFECT":
            key = item_data.get("effect_key") or item_data.get("effect_type")
            if not key:
                raise ValueError("Invalid effect data.")
            profile.active_effect = key
        elif category == "VICTORY":
            key = item_data.get("victory_key") or item_data.get("animation_type")
            if not key:
                raise ValueError("Invalid victory data.")
            profile.active_victory = key
        else:
            raise ValueError("This item cannot be equipped.")

        profile.save()
        return item, key

    @staticmethod
    def unequip_category(user, category):
        """Resets a cosmetic category to its default value."""
        profile = user.profile

        defaults = {
            "THEME": ("active_theme", "vs-dark"),
            "FONT": ("active_font", "Fira Code"),
            "EFFECT": ("active_effect", None),
            "VICTORY": ("active_victory", "default"),
        }

        if category not in defaults:
            raise ValueError("Invalid category.")

        attr, value = defaults[category]
        setattr(profile, attr, value)
        profile.save()
        return True

    @staticmethod
    def upload_image(image_file):
        """Uploads a store item image and returns the URL."""
        safe_name = Path(image_file.name).name
        path = default_storage.save(f"store/{safe_name}", ContentFile(image_file.read()))
        return default_storage.url(path)
