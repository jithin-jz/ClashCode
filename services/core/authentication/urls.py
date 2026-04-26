from django.urls import path

from .views import AccountViewSet, AuthViewSet, OAuthViewSet, OTPViewSet

urlpatterns = [
    # GitHub OAuth
    path(
        "github/",
        OAuthViewSet.as_view({"get": "get_url"}, provider="github"),
        name="github_auth_url",
    ),
    path(
        "github/callback/",
        OAuthViewSet.as_view({"post": "callback"}, provider="github"),
        name="github_callback",
    ),
    # Google OAuth
    path(
        "google/",
        OAuthViewSet.as_view({"get": "get_url"}, provider="google"),
        name="google_auth_url",
    ),
    path(
        "google/callback/",
        OAuthViewSet.as_view({"post": "callback"}, provider="google"),
        name="google_callback",
    ),
    # Auth endpoints
    path("refresh/", AuthViewSet.as_view({"post": "refresh"}), name="refresh_token"),
    path("logout/", AuthViewSet.as_view({"post": "logout"}), name="logout"),
    path(
        "user/delete/",
        AccountViewSet.as_view({"delete": "destroy"}),
        name="delete_account",
    ),
    path("admin/login/", AuthViewSet.as_view({"post": "admin_login"}), name="admin_login"),
    # Email OTP endpoints
    path("otp/request/", OTPViewSet.as_view({"post": "request_otp"}), name="otp_request"),
    path("otp/verify/", OTPViewSet.as_view({"post": "verify_otp"}), name="otp_verify"),
]
