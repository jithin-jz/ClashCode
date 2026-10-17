from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.services import AuthService
from authentication.services.oauth_service import OAuthService
from authentication.utils import decode_token, generate_tokens, get_github_user_email
from project.client_ip import get_client_ip


class LogoutRevocationTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="leaver", email="l@example.com", password="pw")
        self.tokens = generate_tokens(self.user)

    def _cookies(self):
        self.client.cookies[settings.JWT_ACCESS_COOKIE_NAME] = self.tokens["access_token"]
        self.client.cookies[settings.JWT_REFRESH_COOKIE_NAME] = self.tokens["refresh_token"]

    def test_refresh_token_is_unusable_after_logout(self):
        self._cookies()
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user, result = AuthService.refresh_access_token(self.tokens["refresh_token"])
        self.assertIsNone(user)

        access_jti = decode_token(self.tokens["access_token"])["jti"]
        self.assertTrue(AuthService.is_token_blacklisted(access_jti))

    def test_logout_works_with_expired_access_token(self):
        # Only the refresh cookie is left (access cookie already expired in the browser)
        self.client.cookies[settings.JWT_REFRESH_COOKIE_NAME] = self.tokens["refresh_token"]
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user, _ = AuthService.refresh_access_token(self.tokens["refresh_token"])
        self.assertIsNone(user)

    @override_settings(AUTH_REVOCATION_REDIS_ENABLED=True)
    def test_revocations_are_mirrored_for_other_services(self):
        fake_redis = MagicMock()
        with patch("authentication.revocation._redis", return_value=fake_redis):
            AuthService.blacklist_token(decode_token(self.tokens["access_token"]))
            self.user.is_active = False
            self.user.save()

        keys = [call.args[0] for call in fake_redis.set.call_args_list]
        self.assertTrue(any(k.startswith("auth:revoked_jti:") for k in keys))
        self.assertIn(f"auth:disabled_user:{self.user.id}", keys)


class OAuthVerifiedEmailTests(TestCase):
    @patch("authentication.utils.requests.get")
    def test_github_email_ignores_unverified_addresses(self, mock_get):
        mock_get.return_value.json.return_value = [
            {"email": "victim@example.com", "primary": True, "verified": False},
            {"email": "me@example.com", "primary": False, "verified": True},
        ]
        self.assertEqual(get_github_user_email("token"), "me@example.com")

    @patch("authentication.utils.requests.get")
    def test_github_email_none_when_nothing_verified(self, mock_get):
        mock_get.return_value.json.return_value = [{"email": "victim@example.com", "primary": True, "verified": False}]
        self.assertIsNone(get_github_user_email("token"))

    @patch("authentication.services.oauth_service.get_github_user_email", return_value=None)
    @patch("authentication.services.oauth_service.get_github_user")
    def test_github_login_refused_without_verified_email(self, mock_user, _mock_email):
        mock_user.return_value = {"id": 1, "login": "x", "email": "victim@example.com"}
        info = OAuthService._get_provider_user_info("github", "token")
        self.assertIn("error", info)

    @patch("authentication.services.oauth_service.get_google_user")
    def test_google_login_refused_for_unverified_email(self, mock_user):
        mock_user.return_value = {"id": "1", "email": "victim@example.com", "verified_email": False}
        info = OAuthService._get_provider_user_info("google", "token")
        self.assertIn("error", info)

    @patch("authentication.services.oauth_service.get_google_user")
    def test_google_login_accepts_verified_email(self, mock_user):
        mock_user.return_value = {"id": "1", "email": "me@example.com", "verified_email": True, "name": "Me"}
        info = OAuthService._get_provider_user_info("google", "token")
        self.assertEqual(info["email"], "me@example.com")

    @patch("authentication.services.oauth_service.OAuthService._get_provider_user_info")
    @patch("authentication.services.oauth_service.OAuthService._exchange_code_for_token")
    def test_provider_tokens_are_not_persisted(self, mock_exchange, mock_info):
        mock_exchange.return_value = {"access_token": "gho_secret", "refresh_token": "r_secret"}
        mock_info.return_value = {"id": "42", "email": "new@example.com", "username": "new", "name": "", "avatar_url": ""}
        with patch("authentication.services.oauth_service.send_welcome_email_task.delay"):
            user, _ = OAuthService.handle_oauth_login("github", "code")
        user.profile.refresh_from_db()
        self.assertIsNone(user.profile.access_token)
        self.assertIsNone(user.profile.refresh_token)


class ClientIpTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_spoofed_forwarded_for_prefix_is_ignored(self):
        # Client sent "1.1.1.1"; the ALB appended the real address.
        request = self.factory.get("/", HTTP_X_FORWARDED_FOR="1.1.1.1, 203.0.113.7", REMOTE_ADDR="10.0.0.5")
        self.assertEqual(get_client_ip(request), "203.0.113.7")

    def test_without_proxy_header_uses_remote_addr(self):
        request = self.factory.get("/", REMOTE_ADDR="10.0.0.5")
        self.assertEqual(get_client_ip(request), "10.0.0.5")
