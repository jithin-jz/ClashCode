import logging
from django.conf import settings
from django.db import transaction
from rest_framework import views, status, permissions, serializers
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiTypes, inline_serializer

logger = logging.getLogger(__name__)

from xpoint.services import XPService
from .models import Payment
from .serializers import CreateOrderSerializer, VerifyPaymentSerializer
from authentication.throttles import StoreRateThrottle

try:
    import razorpay
except Exception:  # pragma: no cover - optional runtime dependency
    razorpay = None


def _get_razorpay_client():
    if razorpay is None:
        raise RuntimeError("Razorpay SDK is not available")
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise RuntimeError("Razorpay keys are not configured on the server")
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


class CreateOrderView(views.APIView):
    """
    API View to create a Razorpay order for purchasing XP.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [StoreRateThrottle]
    serializer_class = CreateOrderSerializer

    @extend_schema(
        request=CreateOrderSerializer,
        responses={
            201: inline_serializer(
                name="OrderResponse",
                fields={
                    "order_id": serializers.CharField(),
                    "amount": serializers.IntegerField(),
                    "key": serializers.CharField(),
                    "xp_amount": serializers.IntegerField(),
                },
            ),
            400: OpenApiTypes.OBJECT,
            503: OpenApiTypes.OBJECT,
        },
        description="Create a Razorpay order to buy an XP package.",
    )
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        amount_inr = serializer.validated_data["amount"]
        xp_packages_map = {
            49: 50,
            99: 100,
            199: 200,
            249: 250,
            499: 500,
            749: 800,
            999: 1000,
            1999: 2500,
        }

        if amount_inr not in xp_packages_map:
            return Response(
                {"error": "Invalid package amount"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Amount in Paise
        data = {
            "amount": amount_inr * 100,
            "currency": "INR",
            "receipt": f"coc_{request.user.id}_{amount_inr}",
            # Razorpay expects notes values as strings.
            "notes": {"user_id": str(request.user.id)},
        }

        try:
            client = _get_razorpay_client()
            order = client.order.create(data=data)
            xp_to_credit = xp_packages_map[amount_inr]

            Payment.objects.create(
                user=request.user,
                razorpay_order_id=order["id"],
                amount=amount_inr,
                xp_amount=xp_to_credit,
                status="pending",
            )

            return Response(
                {
                    "order_id": order["id"],
                    "amount": data["amount"],
                    "key": settings.RAZORPAY_KEY_ID,
                    "xp_amount": xp_to_credit,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Payment order creation failed: {str(e)}", exc_info=True)
            if "Razorpay SDK is not available" in str(e):
                return Response(
                    {"error": "Payment service is unavailable (Razorpay SDK missing)"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            if "Razorpay keys" in str(e):
                return Response(
                    {"error": "Payment service is unavailable (Razorpay keys missing)"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            if razorpay and isinstance(e, razorpay.errors.BadRequestError):
                return Response(
                    {"error": f"Payment provider rejected the order request: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"error": f"Unable to create payment order: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyPaymentView(views.APIView):
    """
    API View to verify Razorpay payment signatures and award XP.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [StoreRateThrottle]
    serializer_class = VerifyPaymentSerializer

    @extend_schema(
        request=VerifyPaymentSerializer,
        responses={
            200: inline_serializer(
                name="VerifyPaymentResponse",
                fields={
                    "status": serializers.CharField(),
                    "new_xp": serializers.IntegerField(),
                },
            ),
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        description="Verify a completed Razorpay payment and credit XP to the user.",
    )
    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            client = _get_razorpay_client()
            client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": data["razorpay_order_id"],
                    "razorpay_payment_id": data["razorpay_payment_id"],
                    "razorpay_signature": data["razorpay_signature"],
                }
            )

            with transaction.atomic():
                payment = Payment.objects.select_for_update().get(
                    razorpay_order_id=data["razorpay_order_id"]
                )
                if payment.user_id != request.user.id:
                    return Response(
                        {"error": "Order does not belong to authenticated user"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                if payment.status == "success":
                    return Response(
                        {"message": "Payment already processed"},
                        status=status.HTTP_200_OK,
                    )

                payment.razorpay_payment_id = data["razorpay_payment_id"]
                payment.status = "success"
                payment.save()

                new_xp = XPService.add_xp(
                    user=request.user,
                    amount=payment.xp_amount,
                    source=XPService.SOURCE_PURCHASE,
                )

            return Response(
                {"status": "success", "new_xp": new_xp}, status=status.HTTP_200_OK
            )

        except Payment.DoesNotExist:
            return Response(
                {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            if razorpay and isinstance(e, razorpay.errors.SignatureVerificationError):
                return Response(
                    {"error": "Invalid Signature - Payment verification failed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if "Razorpay SDK is not available" in str(e):
                return Response(
                    {"error": "Payment service is temporarily unavailable"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            return Response(
                {"error": "Payment verification failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
