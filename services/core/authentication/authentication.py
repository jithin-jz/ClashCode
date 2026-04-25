from rest_framework import authentication, exceptions
from django.conf import settings
from django.contrib.auth.models import User
from .utils import decode_token


class JWTAuthentication(authentication.BaseAuthentication):
    """
    Custom JWT authentication for Django REST Framework.

    This class verifies the 'Authorization: Bearer <token>' header,
    decodes the JWT, and ensures the associated user is valid and active.
    """

    def authenticate(self, request):
        # 1. Retrieve the Authorization header from the incoming request
        auth_header = request.headers.get("Authorization")

        token = None
        token_source = None
        if auth_header:
            # 2. Extract the prefix and the token string
            try:
                prefix, token = auth_header.split(" ")
                # Only process headers starting with 'bearer'
                if prefix.lower() != "bearer":
                    token = None
                else:
                    token_source = "header"
            except ValueError:
                # Handle malformed headers (e.g., header missing a space)
                token = None

        # Fallback to HttpOnly cookie
        if not token:
            token = request.COOKIES.get(settings.JWT_ACCESS_COOKIE_NAME)
            if token:
                token_source = "cookie"
        if not token:
            return None

        # 3. Decode and validate the token signature and expiration
        payload = decode_token(token)

        # For invalid/expired cookie tokens, treat as anonymous so AllowAny endpoints
        # (like OTP request) are not blocked by stale browser cookies.
        if not payload:
            if token_source == "cookie":
                return None
            raise exceptions.AuthenticationFailed("Invalid or expired token")

        # 4. Enforce token usage policies (e.g., must be an 'access' token)
        if payload.get("type") != "access":
            if token_source == "cookie":
                return None
            raise exceptions.AuthenticationFailed("Invalid token type")

        # 5. Identify and validate the user associated with the token
        try:
            user = User.objects.get(id=payload["user_id"])
        except User.DoesNotExist:
            if token_source == "cookie":
                return None
            raise exceptions.AuthenticationFailed("User not found")

        # 6. Ensure the user account is still permitted to access the system
        if not user.is_active:
            raise exceptions.AuthenticationFailed("User account is disabled.")

        # 7. Return the (user, auth) tuple required by DRF
        # This sets request.user and request.auth in the view
        return (user, token)

    def authenticate_header(self, request):
        return "Bearer"


# JWT Authentication for OpenAPI/Swagger
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class JWTAuthenticationScheme(OpenApiAuthenticationExtension):
    # OpenAPI schema adapter for the custom JWT authentication class

    target_class = (
        "auth.authentication.JWTAuthentication"  # Path to the actual auth class
    )
    name = "JWTAuth"  # Name shown in Swagger's Authorize dialog

    def get_security_definition(self, _auto_schema):
        # Define Bearer JWT authentication for OpenAPI/Swagger
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
