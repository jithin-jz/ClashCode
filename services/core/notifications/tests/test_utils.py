from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from notifications.models import FCMToken
from notifications.utils import send_fcm_push


class NotificationUtilsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="push_user", password="password")
        self.token = FCMToken.objects.create(user=self.user, token="valid-token-123")

    @patch("firebase_admin.messaging.send_each_for_multicast")
    def test_send_fcm_push_success(self, mock_send):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.success_count = 1
        mock_response.failure_count = 0
        mock_response.responses = [MagicMock(success=True)]
        mock_send.return_value = mock_response

        send_fcm_push(self.user, "Hello", "Test body")

        # Verify messaging was called
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        message = args[0]
        self.assertEqual(message.data["title"], "Hello")
        self.assertEqual(message.tokens, ["valid-token-123"])

    @patch("firebase_admin.messaging.send_each_for_multicast")
    def test_send_fcm_push_cleanup_on_failure(self, mock_send):
        # Setup mock response with failure
        mock_response = MagicMock()
        mock_response.success_count = 0
        mock_response.failure_count = 1
        mock_response.responses = [MagicMock(success=False)]
        mock_send.return_value = mock_response

        send_fcm_push(self.user, "Hello", "Fail body")

        # Verify token was deleted
        self.assertEqual(FCMToken.objects.filter(user=self.user).count(), 0)

    def test_send_fcm_push_no_tokens(self):
        other_user = User.objects.create_user(username="no_token_user")
        with patch("firebase_admin.messaging.send_each_for_multicast") as mock_send:
            send_fcm_push(other_user, "Hi", "No token")
            mock_send.assert_not_called()
