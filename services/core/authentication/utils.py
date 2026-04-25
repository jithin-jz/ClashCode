import jwt

import hmac
from hashlib import sha256
import requests
import string
import secrets
from datetime import datetime, timedelta, timezone
from django.conf import settings
from project.media import build_file_url


def generate_otp_code(length=6):
    """Generate a numeric OTP code."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


def hash_otp(email: str, otp: str) -> str:
    normalized = f"{email.lower().strip()}:{otp.strip()}".encode("utf-8")
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), normalized, sha256).hexdigest()


def generate_access_token(user):
    """
    Generate a short-lived JWT access token.
    Contains user identity (id, username, email) but no sensitive data.
    """
    payload = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar_url": (
            build_file_url(user.profile.avatar) if hasattr(user, "profile") else None
        ),
        "exp": datetime.now(timezone.utc)
        + timedelta(seconds=settings.JWT_ACCESS_TOKEN_LIFETIME),
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(
        payload, settings.JWT_PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM
    )


def generate_refresh_token(user):
    """
    Generate a long-lived JWT refresh token.
    Used to obtain new access tokens without re-login.
    """
    payload = {
        "user_id": user.id,
        "exp": datetime.now(timezone.utc)
        + timedelta(seconds=settings.JWT_REFRESH_TOKEN_LIFETIME),
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(
        payload, settings.JWT_PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token):
    """
    Decode and validate a JWT token.
    Returns the payload dict if valid, or None if expired/invalid.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_PUBLIC_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_tokens(user):
    """
    Helper to generate both access and refresh tokens for a user.
    Usage: On Login, Registration, or Token Refresh.
    """
    return {
        "access_token": generate_access_token(user),
        "refresh_token": generate_refresh_token(user),
    }


# GitHub OAuth helpers
def get_github_access_token(code):
    """Exchange authorization code for GitHub access token."""

    response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
        },
        headers={"Accept": "application/json"},
        timeout=10,
    )

    return response.json()


def get_github_user(access_token):
    """Get GitHub user data using access token."""
    response = requests.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
        timeout=10,
    )
    return response.json()


def get_github_user_email(access_token):
    """Get GitHub user's primary email."""
    response = requests.get(
        "https://api.github.com/user/emails",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
        timeout=10,
    )
    emails = response.json()
    for email in emails:
        if email.get("primary"):
            return email.get("email")
    return emails[0].get("email") if emails else None


# Google OAuth helpers
def get_google_access_token(code):
    """Exchange authorization code for Google access token."""

    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )

    return response.json()


def get_google_user(access_token):
    """Get Google user data using access token."""
    response = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    return response.json()
