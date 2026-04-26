from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from store.models import Purchase, StoreItem


class StoreTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="store_user", password="password")
        # Profile is created by signal. Give them some XP.
        self.profile = self.user.profile
        self.profile.xp = 500
        self.profile.save()

        self.client.force_authenticate(user=self.user)

        # Create some items
        self.theme = StoreItem.objects.create(
            name="Dracula",
            cost=200,
            category="THEME",
            item_data={"theme_key": "dracula"},
            icon_name="moon",
        )
        self.font = StoreItem.objects.create(
            name="Mono",
            cost=100,
            category="FONT",
            item_data={"font_family": "Monospace"},
            icon_name="type",
        )
        self.inactive = StoreItem.objects.create(name="Old", cost=50, category="THEME", is_active=False, icon_name="clock")

    def test_list_active_items(self):
        url = reverse("store-item-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see 2 active items
        self.assertEqual(len(response.data), 2)
        item_names = [item["name"] for item in response.data]
        self.assertIn("Dracula", item_names)
        self.assertNotIn("Old", item_names)

    def test_purchase_item_success(self):
        url = reverse("store-buy", kwargs={"pk": self.theme.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["remaining_xp"], 300)  # 500 - 200
        self.assertTrue(Purchase.objects.filter(user=self.user, item=self.theme).exists())

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.xp, 300)

    def test_insufficient_xp_fails(self):
        # Set XP lower than cost
        self.profile.xp = 50
        self.profile.save()

        url = reverse("store-buy", kwargs={"pk": self.theme.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Insufficient XP", response.data["error"])

    def test_duplicate_purchase_fails(self):
        url = reverse("store-buy", kwargs={"pk": self.theme.id})
        # Buy first time
        self.client.post(url)

        # Try buying again
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "You already own this item.")

    def test_equip_item_success(self):
        # 1. Buy it first
        Purchase.objects.create(user=self.user, item=self.theme)

        # 2. Equip it
        url = reverse("store-equip")
        response = self.client.post(url, {"item_id": self.theme.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["active_theme"], "dracula")

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.active_theme, "dracula")

    def test_equip_without_ownership_fails(self):
        url = reverse("store-equip")
        response = self.client.post(url, {"item_id": self.theme.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "You do not own this item.")

    def test_unequip_item(self):
        self.profile.active_theme = "dracula"
        self.profile.save()

        url = reverse("store-unequip")
        response = self.client.post(url, {"category": "THEME"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.active_theme, "vs-dark")  # default

    def test_purchased_items_list(self):
        Purchase.objects.create(user=self.user, item=self.theme)

        url = reverse("store-purchased")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["purchased_items"]), 1)
        self.assertEqual(response.data["purchased_items"][0]["name"], "Dracula")
