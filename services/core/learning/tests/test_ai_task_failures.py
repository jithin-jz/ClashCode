from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase

from learning.tasks.ai import generate_ai_analysis_task, generate_ai_hint_task


class AITaskFailurePublishingTests(TestCase):
    """A failed AI call must still notify the browser, otherwise the UI waits until timeout."""

    def setUp(self):
        cache.clear()

    @patch("learning.tasks.ai._publish_task_result")
    @patch("learning.tasks.ai.requests.post")
    def test_hint_task_publishes_on_upstream_error(self, mock_post, mock_publish):
        mock_post.return_value = MagicMock(status_code=500)
        result = generate_ai_hint_task.apply(
            kwargs={
                "user_id": 1,
                "challenge_id": 1,
                "challenge_slug": "s",
                "user_code": "x",
                "hint_level": 1,
                "user_xp": 0,
            }
        ).get()

        self.assertFalse(result["ok"])
        mock_publish.assert_called_once()
        self.assertEqual(mock_publish.call_args.args[2], "hint")

    @patch("learning.tasks.ai._publish_task_result")
    @patch("learning.tasks.ai.requests.post")
    def test_analysis_task_publishes_on_upstream_error(self, mock_post, mock_publish):
        mock_post.return_value = MagicMock(status_code=403)
        result = generate_ai_analysis_task.apply(
            kwargs={"user_id": 1, "challenge_id": 1, "challenge_slug": "s", "user_code": "x"}
        ).get()

        self.assertFalse(result["ok"])
        self.assertEqual(result["status_code"], 502)
        mock_publish.assert_called_once()
