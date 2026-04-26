import logging
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiTypes

from authentication.throttles import StoreRateThrottle
from .serializers import (
    CreateOrderSerializer, 
    VerifyPaymentSerializer,
    OrderResponseSerializer,
    VerifyPaymentResponseSerializer
)
from .services import PaymentService

logger = logging.getLogger(__name__)

class CreateOrderView(generics.GenericAPIView):
    """
    API View to create a Razorpay order for purchasing XP.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [StoreRateThrottle]
    serializer_class = CreateOrderSerializer

    @extend_schema(
        request=CreateOrderSerializer,
        responses={
            201: OrderResponseSerializer,
            400: OpenApiTypes.OBJECT,
            503: OpenApiTypes.OBJECT,
        },
        description="Create a Razorpay order to buy an XP package.",
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order_details = PaymentService.create_order(
                user=request.user,
                amount_inr=serializer.validated_data["amount"]
            )
            return Response(order_details, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as e:
            logger.error(f"Payment system error: {e}")
            return Response({"error": "Payment service is currently unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.error(f"Unexpected payment error: {e}", exc_info=True)
            return Response({"error": "An unexpected error occurred while creating the order."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyPaymentView(generics.GenericAPIView):
    """
    API View to verify Razorpay payment signatures and award XP.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [StoreRateThrottle]
    serializer_class = VerifyPaymentSerializer

    @extend_schema(
        request=VerifyPaymentSerializer,
        responses={
            200: VerifyPaymentResponseSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        description="Verify a completed Razorpay payment and credit XP to the user.",
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            result = PaymentService.verify_payment(
                user=request.user,
                order_id=data["razorpay_order_id"],
                payment_id=data["razorpay_payment_id"],
                signature=data["razorpay_signature"]
            )
            return Response(result, status=status.HTTP_200_OK)

        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except (ValueError, Exception) as e:
            error_msg = str(e)
            logger.warning(f"Payment verification failed for user {request.user.id}: {error_msg}")
            
            if "SignatureVerificationError" in error_msg or "Invalid Signature" in error_msg:
                return Response({"error": "Payment verification failed. Invalid signature."}, status=status.HTTP_400_BAD_REQUEST)
            
            if "not found" in error_msg.lower():
                return Response({"error": "Order record not found."}, status=status.HTTP_404_NOT_FOUND)
                
            return Response({"error": "Payment verification failed."}, status=status.HTTP_400_BAD_REQUEST)
