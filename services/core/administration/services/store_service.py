from store.models import StoreItem

from administration.utils import log_admin_action


class StoreService:
    @staticmethod
    def duplicate_store_item(admin, item_id, request=None):
        """Duplicates an existing store item."""
        item = StoreItem.objects.filter(id=item_id).first()
        if not item:
            return None, "Store item not found.", 404

        duplicate = StoreItem.objects.create(
            name=f"{item.name} Copy",
            description=item.description,
            cost=item.cost,
            icon_name=item.icon_name,
            category=item.category,
            image=item.image,
            item_data=item.item_data,
            is_active=False,
            featured=False,
        )

        log_admin_action(
            admin=admin,
            action="DUPLICATE_STORE_ITEM",
            request=request,
            details={"source_item_id": item.id, "duplicate_item_id": duplicate.id},
        )
        return duplicate, None, 200
