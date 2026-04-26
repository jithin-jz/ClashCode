import logging

from drf_spectacular.utils import extend_schema
from rest_framework import decorators, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import UserCertificate
from .serializers import (
    CertificateEligibilitySerializer,
    CertificateVerificationSerializer,
    UserCertificateSerializer,
)
from .services import CertificateService

logger = logging.getLogger(__name__)


class CertificateViewSet(viewsets.ViewSet):
    """
    ViewSet for certificate generation and verification.
    """

    def get_permissions(self):
        if self.action == "verify":
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(
        responses={200: UserCertificateSerializer},
        description="Get or generate the authenticated user's completion certificate.",
    )
    @decorators.action(detail=False, methods=["get"])
    def my_certificate(self, request):
        user = request.user
        is_eligible = CertificateService.is_eligible(user)
        existing_certificate = UserCertificate.objects.filter(user=user).first()

        # 1. Existing certificate and still eligible (check for count update)
        if existing_certificate and is_eligible:
            current_completed = CertificateService.get_completed_count(user)
            if existing_certificate.completion_count != current_completed:
                existing_certificate.completion_count = current_completed
                existing_certificate.save(update_fields=["completion_count"])

            serializer = UserCertificateSerializer(existing_certificate, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        # 2. Not eligible yet - return status
        if not is_eligible:
            status_info = CertificateService.get_eligibility_status(user)
            serializer = CertificateEligibilitySerializer(status_info)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # 3. Eligible but no certificate yet - Generate
        try:
            certificate = CertificateService.get_or_create_certificate(user)
            serializer = UserCertificateSerializer(certificate, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            logger.exception("Failed to generate certificate for %s", user.username)
            return Response(
                {"error": "Failed to generate certificate. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        responses={200: CertificateVerificationSerializer},
        description="Verify a certificate by its unique ID.",
    )
    @decorators.action(detail=False, methods=["get"], url_path="verify/(?P<certificate_id>[^/.]+)")
    def verify(self, request, certificate_id=None):
        certificate, found = CertificateService.verify_certificate(certificate_id, request=request)

        data = {
            "valid": found and certificate.is_valid if certificate else False,
            "certificate": certificate if found else None,
        }

        serializer = CertificateVerificationSerializer(data, context={"request": request})
        return Response(
            serializer.data,
            status=status.HTTP_200_OK if found else status.HTTP_404_NOT_FOUND,
        )

    @extend_schema(
        responses={200: CertificateEligibilitySerializer},
        description="Check if the authenticated user is eligible for a certificate.",
    )
    @decorators.action(detail=False, methods=["get"])
    def check_eligibility(self, request):
        status_info = CertificateService.get_eligibility_status(request.user)
        serializer = CertificateEligibilitySerializer(status_info)
        return Response(serializer.data, status=status.HTTP_200_OK)
