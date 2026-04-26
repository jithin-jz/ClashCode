from django.db.models import Sum
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import XPTransaction
from .serializers import XPStatsSerializer, XPTransactionSerializer


class XPViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing XP transaction history and statistics.
    """

    serializer_class = XPTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return XPTransaction.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Returns XP statistics for the current user."""
        user = request.user
        queryset = self.get_queryset()

        stats = {
            "current_xp": user.profile.xp,
            "total_earned": queryset.filter(amount__gt=0).aggregate(Sum("amount"))["amount__sum"] or 0,
            "total_spent": abs(queryset.filter(amount__lt=0).aggregate(Sum("amount"))["amount__sum"] or 0),
            "transaction_count": queryset.count(),
        }

        serializer = XPStatsSerializer(stats)
        return Response(serializer.data)
