from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from administration.permissions import IsAdminUser
from administration.services.store_service import StoreService


class StoreItemDuplicateView(APIView):
    """View to duplicate an existing store item."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
        description="Duplicate an existing store item to speed up admin catalog management.",
    )
    def post(self, request, item_id):
        duplicate, error, code = StoreService.duplicate_store_item(
            admin=request.user, item_id=item_id, request=request
        )

        if error:
            return Response({"error": error}, status=code)

        return Response(
            {"id": duplicate.id, "message": "Store item duplicated."},
            status=status.HTTP_200_OK,
        )
