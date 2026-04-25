from rest_framework import serializers
from django.contrib.auth import authenticate
from users.serializers import UserSerializer


class AuthTokenSerializer(serializers.Serializer):
    """
    Response serializer for successful authentication.
    Bundles tokens with user data for frontend bootstrapping.

    Why bundle user data?
    To avoid an extra network round-trip. When a user logs in, the frontend
    immediately needs their profile (name, avatar, etc.) to render the UI.
    """

    # Short-lived token for authenticated API access (usually 5-15 mins)
    access_token = serializers.CharField(help_text="JWT access token")

    # Long-lived token used to refresh access tokens (usually 1-7 days)
    refresh_token = serializers.CharField(help_text="JWT refresh token")

    # Embedded user payload to avoid extra /me call on login
    user = UserSerializer(read_only=True)


class RefreshTokenSerializer(serializers.Serializer):
    """
    Request serializer for refreshing access tokens.
    Only refresh_token is required; user context is inferred server-side.
    """

    refresh_token = serializers.CharField()


class AdminLoginSerializer(serializers.Serializer):
    """
    Dedicated serializer for admin-only authentication.
    Explicitly blocks non-staff users even with valid credentials.
    """

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        # Extract credentials from payload
        username = data.get("username")
        password = data.get("password")

        if username and password:
            # Delegate credential verification to Django auth backend
            user = authenticate(
                request=self.context.get("request"),
                username=username,
                password=password,
            )

            # Reject invalid credentials
            if not user:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials."
                )

            # Enforce admin-only access
            if not (user.is_staff or user.is_superuser):
                raise serializers.ValidationError(
                    "You do not have permission to access the admin area."
                )

            # Attach authenticated user to validated data
            data["user"] = user
        else:
            # Enforce presence of both username and password
            raise serializers.ValidationError('Must include "username" and "password".')

        return data


class OAuthCodeSerializer(serializers.Serializer):
    """Serializer for OAuth callback receiving an authorization code."""

    code = serializers.CharField(
        required=True, help_text="Authorization code from the provider."
    )


class OAuthURLSerializer(serializers.Serializer):
    """Serializer for returning the OAuth authorization URL."""

    url = serializers.URLField(help_text="Redirect URL for OAuth provider.")


class OTPRequestSerializer(serializers.Serializer):
    """
    Validator for OTP request payload.
    Ensures email is provided and valid.
    """

    email = serializers.EmailField(required=True)


class OTPVerifySerializer(serializers.Serializer):
    """
    Validator for OTP verification payload.
    Requires both email and a 6-digit OTP code.
    """

    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)
