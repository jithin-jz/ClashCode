from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from posts.models import Post
from users.models import UserFollow


class NotificationSignalTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username="author", password="password")
        self.actor = User.objects.create_user(username="actor", password="password")

    @patch("notifications.services.send_push_notification_task.delay")
    def test_like_signal_enqueues_push_task(self, mock_delay):
        post = Post.objects.create(user=self.author, caption="hello", image="posts/test.jpg")

        post.likes.add(self.actor)

        mock_delay.assert_called_once()
        args, _ = mock_delay.call_args
        self.assertEqual(args[0], self.author.id)
        self.assertIn("liked your post", args[2])

    @patch("notifications.services.send_push_notification_task.delay")
    def test_follow_signal_enqueues_push_task(self, mock_delay):
        UserFollow.objects.create(follower=self.actor, following=self.author)

        mock_delay.assert_called_once_with(
            self.author.id,
            "New Follower!",
            f"{self.actor.username} started following you.",
        )
