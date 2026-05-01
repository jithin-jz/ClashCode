import logging

from authentication.throttles import StoreRateThrottle
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import OpenApiTypes, extend_schema, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Purchase, StoreItem
from .serializers import (
    EquipItemRequestSerializer,
    InventoryResponseSerializer,
    PurchaseResponseSerializer,
    StoreItemSerializer,
    UnequipItemRequestSerializer,
)
from .services import StoreService

logger = logging.getLogger(__name__)


@method_decorator(never_cache, name="dispatch")
class StoreItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing store items (Themes, Fonts, Effects, etc.).
    """

    serializer_class = StoreItemSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return StoreItem.objects.all().order_by("-created_at")
        return StoreItem.objects.filter(is_active=True).order_by("-created_at")

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]


class PurchaseItemView(APIView):
    """
    API View to purchase a store item using XP.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [StoreRateThrottle]

    @extend_schema(
        request=None,
        responses={201: PurchaseResponseSerializer, 400: OpenApiTypes.OBJECT},
        description="Purchase a store item using user's accumulated XP.",
    )
    def post(self, request, pk=None):
        try:
            item, remaining_xp = StoreService.purchase_item(request.user, pk)

            return Response(
                {
                    "status": "success",
                    "message": f"Purchased {item.name}",
                    "remaining_xp": remaining_xp,
                    "item": StoreItemSerializer(item, context={"request": request}).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Purchase error: {e}")
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PurchasedItemsView(APIView):
    """
    API View to list all items purchased by the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: InventoryResponseSerializer},
        description="Get a list of all purchased items and the currently equipped cosmetics.",
    )
    def get(self, request):
        purchases = (
            Purchase.objects.select_related("item")
            .filter(user=request.user, item__is_active=True)
            .order_by("-purchased_at")
        )

        items = [p.item for p in purchases]
        profile = request.user.profile

        return Response(
            {
                "purchased_items": StoreItemSerializer(items, many=True, context={"request": request}).data,
                "equipped_items": {
                    "theme": profile.active_theme,
                    "font": profile.active_font,
                    "effect": profile.active_effect,
                    "victory": profile.active_victory,
                },
            },
            status=status.HTTP_200_OK,
        )


class EquipItemView(APIView):
    """
    API View to equip a purchased cosmetic item.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=EquipItemRequestSerializer,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
        description="Equip a purchased cosmetic item (Theme, Font, Effect, Victory animation).",
    )
    def post(self, request):
        serializer = EquipItemRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            item, active_key = StoreService.equip_item(request.user, serializer.validated_data["item_id"])

            return Response(
                {
                    "status": "success",
                    "message": f"Equipped {item.name}",
                    f"active_{item.category.lower()}": active_key,
                },
                status=status.HTTP_200_OK,
            )

        except (ValueError, PermissionError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UnequipItemView(APIView):
    """
    API View to unequip items from a specific category.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=UnequipItemRequestSerializer,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
        description="Reset a cosmetic category to its default value.",
    )
    def post(self, request):
        serializer = UnequipItemRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            category = serializer.validated_data["category"]
            StoreService.unequip_category(request.user, category)
            return Response(
                {"status": "success", "message": f"Unequipped {category}"},
                status=status.HTTP_200_OK,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ImageUploadView(APIView):
    """
    API View for admins to upload images for store items.
    """

    permission_classes = [IsAdminUser]

    @extend_schema(
        request={"multipart/form-data": inline_serializer(name="Upload", fields={"image": serializers.FileField()})},
        responses={201: OpenApiTypes.OBJECT},
        description="Upload an image asset for store items (Admin only).",
    )
    def post(self, request):
        file_obj = request.FILES.get("image")
        if not file_obj:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        url = StoreService.upload_image(file_obj)
        return Response({"url": url}, status=status.HTTP_201_CREATED)
