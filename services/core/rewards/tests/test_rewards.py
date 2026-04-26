from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from rewards.models import DailyCheckIn


class RewardsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reward_user", password="password")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("rewards:check-in")

    def test_daily_checkin_success(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["cycle_day"], 1)
        self.assertEqual(response.data["xp_earned"], 5)
        self.assertEqual(DailyCheckIn.objects.count(), 1)

    def test_double_checkin_fails(self):
        # First check-in
        self.client.post(self.url)
        # Second check-in on the same day
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Already checked in today")

    def test_get_checkin_status(self):
        # Before check-in
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["checked_in_today"])

        # After check-in
        self.client.post(self.url)
        response = self.client.get(self.url)
        self.assertTrue(response.data["checked_in_today"])
        self.assertEqual(response.data["cycle_day"], 1)

    def test_streak_cycle_progression(self):
        # Mock day 1
        self.client.post(self.url)
        self.user.profile.reward_cycle_start_date = timezone.now().date() - timedelta(days=1)
        self.user.profile.save()

        # Delete today's check-in to allow another post (simulating it's now a new day)
        DailyCheckIn.objects.filter(user=self.user, check_in_date=timezone.now().date()).delete()

        # Now it should be day 2
        response = self.client.get(self.url)
        self.assertEqual(response.data["cycle_day"], 2)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["cycle_day"], 2)
        self.assertEqual(response.data["xp_earned"], 10)

    def test_cycle_reset_after_7_days(self):
        # Start cycle 8 days ago
        self.user.profile.reward_cycle_start_date = timezone.now().date() - timedelta(days=8)
        self.user.profile.save()

        # Should reset to day 1
        response = self.client.get(self.url)
        self.assertEqual(response.data["cycle_day"], 1)

        response = self.client.post(self.url)
        self.assertEqual(response.data["cycle_day"], 1)
        self.assertEqual(response.data["xp_earned"], 5)

    def test_missed_day_logic(self):
        # Day 1: Check-in
        self.client.post(self.url)

        # Fast forward 2 days (skip day 2, now on day 3)
        self.user.profile.reward_cycle_start_date = timezone.now().date() - timedelta(days=2)
        self.user.profile.save()

        # Delete today's check-in to allow another post
        DailyCheckIn.objects.filter(user=self.user, check_in_date=timezone.now().date()).delete()

        response = self.client.get(self.url)
        self.assertEqual(response.data["cycle_day"], 3)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["cycle_day"], 3)
        self.assertEqual(response.data["xp_earned"], 15)

        # Total check-ins should be 1 (because we deleted the first one to simulate)
        # Actually better to keep the first one but move it back.
        # But since it's auto_now_add, let's just assert we have 1 now.
        self.assertEqual(DailyCheckIn.objects.count(), 1)
