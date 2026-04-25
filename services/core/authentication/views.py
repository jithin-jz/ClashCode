from urllib.parse import urlencode
import logging
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiTypes, inline_serializer
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response
from rest_framework.views import APIView

from .throttles import AuthRateThrottle, SensitiveOperationThrottle

from users.serializers import UserSerializer
from .serializers import (
    RefreshTokenSerializer,
    AdminLoginSerializer,
    OAuthCodeSerializer,
    OAuthURLSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
)
from .services import AuthService
from .utils import generate_access_token, decode_token, generate_tokens

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


# --- OAuth Views ---


class GitHubAuthURLView(APIView):
    """
    Step 1 of GitHub OAuth: Get the redirect URL.
    """

    permission_classes = [AllowAny]
    throttle_classes = []
    serializer_class = OAuthURLSerializer

    @extend_schema(
        responses={200: OAuthURLSerializer},
        description="Get the GitHub OAuth authorization URL to initiate the login process.",
    )
    def get(self, request):
        state = request.query_params.get("state")
        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
            "scope": "user:email",  # Request email access
        }
        if state:
            params["state"] = state

        url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
        return Response({"url": url}, status=status.HTTP_200_OK)


class GitHubCallbackView(APIView):
    """
    Step 2 of GitHub OAuth: Handle the callback code.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]
    serializer_class = OAuthCodeSerializer

    @extend_schema(
        request=OAuthCodeSerializer,
        responses={
            200: inline_serializer(
                name="AuthResponse",
                fields={
                    "user": UserSerializer(),
                },
            ),
            400: OpenApiTypes.OBJECT,
        },
        description="Exchange GitHub authorization code for JWT tokens and user profile.",
    )
    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response(
                {"error": "Authorization code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delegate to Service Layer
        user, result = AuthService.handle_oauth_login("github", code)

        if not user:
            # Login Failed (result contains error dict)
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return _auth_success_response(request, user, result)


class GoogleAuthURLView(APIView):
    """Return the Google OAuth authorization URL."""

    permission_classes = [AllowAny]
    throttle_classes = []
    serializer_class = OAuthURLSerializer

    @extend_schema(
        responses={200: OAuthURLSerializer},
        description="Get the Google OAuth authorization URL to initiate the login process.",
    )
    def get(self, request):
        state = request.query_params.get("state")
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
            "access_type": "offline",
            "prompt": "select_account",
        }
        if state:
            params["state"] = state

        url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return Response({"url": url}, status=status.HTTP_200_OK)


class GoogleCallbackView(APIView):
    """Handle Google OAuth callback."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]
    serializer_class = OAuthCodeSerializer

    @extend_schema(
        request=OAuthCodeSerializer,
        responses={
            200: inline_serializer(
                name="GoogleAuthResponse",
                fields={
                    "user": UserSerializer(),
                },
            ),
            400: OpenApiTypes.OBJECT,
        },
        description="Exchange Google authorization code for JWT tokens and user profile.",
    )
    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response(
                {"error": "Authorization code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, result = AuthService.handle_oauth_login("google", code)

        if not user:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return _auth_success_response(request, user, result)


# --- General User Views ---


class RefreshTokenView(APIView):
    """Refresh the access token using a refresh token."""

    permission_classes = [AllowAny]
    serializer_class = RefreshTokenSerializer

    @extend_schema(
        request=RefreshTokenSerializer,
        responses={
            200: inline_serializer(
                name="RefreshResponse",
                fields={
                    "user": UserSerializer(),
                },
            ),
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        description="Refresh the access token using a valid refresh token (from body or cookie).",
    )
    def post(self, request):
        token = request.data.get("refresh_token") or request.COOKIES.get(
            settings.JWT_REFRESH_COOKIE_NAME
        )
        if not token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payload = decode_token(token)

        if not payload:
            return Response(
                {"error": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if payload.get("type") != "refresh":
            return Response(
                {"error": "Invalid token type"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            user = User.objects.get(id=payload["user_id"])
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"error": "User account is disabled."}, status=status.HTTP_403_FORBIDDEN
            )

        new_access_token = generate_access_token(user)

        payload = {"user": UserSerializer(user, context={"request": request}).data}
        if getattr(settings, "JWT_RETURN_TOKENS_IN_BODY", False):
            payload["access_token"] = new_access_token

        response = Response(payload, status=status.HTTP_200_OK)
        _set_auth_cookies(response, access_token=new_access_token)
        return response


class LogoutView(APIView):
    """Logout the user (client should delete tokens)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: OpenApiTypes.OBJECT},
        description="Logout the user and clear authentication cookies.",
    )
    def post(self, request):
        response = Response(
            {"message": "Successfully logged out"}, status=status.HTTP_200_OK
        )
        _clear_auth_cookies(response)
        return response


class DeleteAccountView(APIView):
    """View to delete the user account."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [SensitiveOperationThrottle]

    @extend_schema(
        request=None,
        responses={200: OpenApiTypes.OBJECT},
        description="Permanently delete the authenticated user account.",
    )
    def delete(self, request):
        user_id = request.user.id
        try:
            with transaction.atomic():
                # Explicitly fetch fresh user instance and lock the row
                user = User.objects.select_for_update().get(id=user_id)
                user.delete()

            response = Response(
                {"message": "Account deleted successfully"}, status=status.HTTP_200_OK
            )
            _clear_auth_cookies(response)
            return response

        except Exception as e:
            # Table missing error? Run 'python manage.py migrate' in production.
            logger.exception(f"DeleteAccount failed for user_id={user_id}")
            return Response(
                {
                    "error": "Failed to delete account. Please try again or contact support."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# --- Admin Views ---


class AdminLoginView(APIView):
    """Admin login view."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]
    serializer_class = AdminLoginSerializer

    @extend_schema(
        request=AdminLoginSerializer,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
        description="Authenticate an administrator using username and password.",
    )
    def post(self, request):
        serializer = AdminLoginSerializer(
            data=request.data, context={"request": request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]
        tokens = generate_tokens(user)

        return _auth_success_response(request, user, tokens)


# --- OTP Views ---


class OTPRequestView(APIView):
    """
    Step 1 of Email OTP Login: Request a One-Time Password.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]
    throttle_scope = "otp"
    serializer_class = OTPRequestSerializer

    @extend_schema(
        request=OTPRequestSerializer,
        responses={200: OpenApiTypes.OBJECT, 429: OpenApiTypes.OBJECT},
        description="Request a One-Time Password (OTP) to be sent to the provided email address.",
    )
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        try:
            AuthService.request_otp(email)
        except ValidationError as exc:
            message = exc.messages[0] if getattr(exc, "messages", None) else str(exc)
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
            if "deliver OTP" in message:
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return Response({"error": message}, status=status_code)
        except Exception:
            logger.exception("OTP request failed for email=%s", email)
            return Response(
                {"error": "OTP service is temporarily unavailable. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


class OTPVerifyView(APIView):
    """
    Step 2 of Email OTP Login: Verify the One-Time Password.
    """

    permission_classes = [AllowAny]
    throttle_classes = [SensitiveOperationThrottle]
    serializer_class = OTPVerifySerializer

    @extend_schema(
        request=OTPVerifySerializer,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
        description="Verify the OTP sent to email and receive JWT tokens.",
    )
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        user, result = AuthService.verify_otp(email, otp)

        if not user:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return _auth_success_response(request, user, result)
