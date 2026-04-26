import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from drf_spectacular.utils import OpenApiTypes, extend_schema, inline_serializer
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from users.serializers import UserSerializer

from .serializers import (
    AdminLoginSerializer,
    OAuthCodeSerializer,
    OAuthURLSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    RefreshTokenSerializer,
)
from .services import AuthService
from .throttles import AuthRateThrottle, SensitiveOperationThrottle
from .utils import generate_tokens

logger = logging.getLogger(__name__)


def _set_auth_cookies(response, access_token: str, refresh_token: str | None = None):
    response.set_cookie(
        settings.JWT_ACCESS_COOKIE_NAME,
        access_token,
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        max_age=settings.JWT_ACCESS_TOKEN_LIFETIME,
        path="/",
    )
    if refresh_token:
        response.set_cookie(
            settings.JWT_REFRESH_COOKIE_NAME,
            refresh_token,
            httponly=True,
            secure=settings.JWT_COOKIE_SECURE,
            samesite=settings.JWT_COOKIE_SAMESITE,
            max_age=settings.JWT_REFRESH_TOKEN_LIFETIME,
            path="/",
        )


def _clear_auth_cookies(response):
    response.delete_cookie(settings.JWT_ACCESS_COOKIE_NAME, path="/")
    response.delete_cookie(settings.JWT_REFRESH_COOKIE_NAME, path="/")


def _auth_success_response(request, user, result):
    payload = {"user": UserSerializer(user, context={"request": request}).data}
    if getattr(settings, "JWT_RETURN_TOKENS_IN_BODY", False):
        payload["access_token"] = result["access_token"]
        payload["refresh_token"] = result["refresh_token"]
    response = Response(payload, status=status.HTTP_200_OK)
    _set_auth_cookies(
        response,
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
    )
    return response


class OAuthViewSet(viewsets.ViewSet):
    """
    Unified ViewSet for OAuth operations (GitHub, Google, etc.)
    """

    permission_classes = [AllowAny]
    provider = None

    @extend_schema(
        responses={200: OAuthURLSerializer},
        description="Get the OAuth authorization URL for a specific provider.",
    )
    @action(detail=False, methods=["get"])
    def get_url(self, request, provider=None):
        # Support both URL kwarg and as_view() initialization kwarg
        provider = provider or getattr(self, "provider", None)

        state = request.query_params.get("state")
        if provider == "github":
            url = AuthService.get_github_auth_url(state)
        elif provider == "google":
            url = AuthService.get_google_auth_url(state)
        else:
            return Response({"error": "Invalid provider"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"url": url}, status=status.HTTP_200_OK)

    @extend_schema(
        request=OAuthCodeSerializer,
        responses={200: inline_serializer(name="OAuthResponse", fields={"user": UserSerializer()})},
        description="Exchange authorization code for tokens and user profile.",
    )
    @action(detail=False, methods=["post"], throttle_classes=[AuthRateThrottle])
    def callback(self, request, provider=None):
        provider = provider or getattr(self, "provider", None)

        code = request.data.get("code")
        if not code:
            return Response(
                {"error": "Authorization code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, result = AuthService.handle_oauth_login(provider, code, request=request)
        if not user:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return _auth_success_response(request, user, result)


class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet for core authentication actions: Login, Refresh, Logout.
    """

    def get_permissions(self):
        if self.action == "logout":
            return [IsAuthenticated()]
        return [AllowAny()]

    @extend_schema(
        request=RefreshTokenSerializer,
        responses={200: inline_serializer(name="RefreshResponse", fields={"user": UserSerializer()})},
        description="Refresh the access token using a valid refresh token.",
    )
    @action(detail=False, methods=["post"])
    def refresh(self, request):
        token = request.data.get("refresh_token") or request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        user, result = AuthService.refresh_access_token(token)

        if not user:
            status_code = status.HTTP_401_UNAUTHORIZED
            if "disabled" in result:
                status_code = status.HTTP_403_FORBIDDEN
            elif "required" in result:
                status_code = status.HTTP_400_BAD_REQUEST
            return Response({"error": result}, status=status_code)

        new_tokens = AuthService.rotate_refresh_token(user, result, request=request)
        return _auth_success_response(request, user, new_tokens)

    @extend_schema(
        request=None,
        responses={200: OpenApiTypes.OBJECT},
        description="Logout the user and clear cookies.",
    )
    @action(detail=False, methods=["post"])
    def logout(self, request):
        AuthService.handle_logout(request)
        response = Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
        _clear_auth_cookies(response)
        return response

    @extend_schema(
        request=AdminLoginSerializer,
        responses={200: OpenApiTypes.OBJECT},
        description="Authenticate an administrator.",
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="admin/login",
        throttle_classes=[AuthRateThrottle],
    )
    def admin_login(self, request):
        serializer = AdminLoginSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]
        tokens = generate_tokens(user)
        return _auth_success_response(request, user, tokens)


class OTPViewSet(viewsets.ViewSet):
    """
    ViewSet for Email OTP authentication.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        request=OTPRequestSerializer,
        responses={200: OpenApiTypes.OBJECT},
        description="Request a One-Time Password (OTP).",
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="request",
        throttle_classes=[AnonRateThrottle],
    )
    def request_otp(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        try:
            AuthService.request_otp(email)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except Exception:
            return Response(
                {"error": "OTP service unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)

    @extend_schema(
        request=OTPVerifySerializer,
        responses={200: OpenApiTypes.OBJECT},
        description="Verify OTP and receive tokens.",
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="verify",
        throttle_classes=[SensitiveOperationThrottle],
    )
    def verify_otp(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user, result = AuthService.verify_otp(
            serializer.validated_data["email"],
            serializer.validated_data["otp"],
            request=request,
        )
        if not user:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return _auth_success_response(request, user, result)


class AccountViewSet(viewsets.ViewSet):
    """
    ViewSet for user account lifecycle management.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [SensitiveOperationThrottle]

    @extend_schema(
        request=None,
        responses={200: OpenApiTypes.OBJECT},
        description="Permanently delete the authenticated user account.",
    )
    def destroy(self, request, pk=None):
        success, error = AuthService.delete_user_account(request.user.id, request=request)
        if not success:
            return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response = Response({"message": "Account deleted successfully"}, status=status.HTTP_200_OK)
        _clear_auth_cookies(response)
        return response
