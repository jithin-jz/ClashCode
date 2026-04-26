from challenges.models import Challenge, UserProgress
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from learning.tasks import update_leaderboard_cache


class LearningTaskTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user1 = User.objects.create_user(username="user1", email="u1@ex.com")
        self.user2 = User.objects.create_user(username="user2", email="u2@ex.com")

        self.c1 = Challenge.objects.create(title="C1", slug="c1", order=1)
        self.c2 = Challenge.objects.create(title="C2", slug="c2", order=2)

        # User 1 completes both
        UserProgress.objects.create(user=self.user1, challenge=self.c1, status=UserProgress.Status.COMPLETED)
        UserProgress.objects.create(user=self.user1, challenge=self.c2, status=UserProgress.Status.COMPLETED)

        # User 2 completes one
        UserProgress.objects.create(user=self.user2, challenge=self.c1, status=UserProgress.Status.COMPLETED)

    def test_update_leaderboard_cache(self):
        # Run the task synchronously
        update_leaderboard_cache()

        leaderboard_data = cache.get("leaderboard_data")
        self.assertIsNotNone(leaderboard_data)
        self.assertEqual(len(leaderboard_data), 2)

        # user1 should be first (2 completions)
        self.assertEqual(leaderboard_data[0]["username"], "user1")
        self.assertEqual(leaderboard_data[0]["completed_levels"], 2)

        # user2 should be second (1 completion)
        self.assertEqual(leaderboard_data[1]["username"], "user2")
        self.assertEqual(leaderboard_data[1]["completed_levels"], 1)
