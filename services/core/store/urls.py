from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    EquipItemView,
    ImageUploadView,
    PurchasedItemsView,
    PurchaseItemView,
    StoreItemViewSet,
    UnequipItemView,
)

router = DefaultRouter()
router.register(r"items", StoreItemViewSet, basename="store-item")

urlpatterns = [
    path("buy/<int:pk>/", PurchaseItemView.as_view(), name="store-buy"),
    path("purchased/", PurchasedItemsView.as_view(), name="store-purchased"),
    path("upload/", ImageUploadView.as_view(), name="store-upload"),
    path("equip/", EquipItemView.as_view(), name="store-equip"),
    path("unequip/", UnequipItemView.as_view(), name="store-unequip"),
    path("", include(router.urls)),
]
