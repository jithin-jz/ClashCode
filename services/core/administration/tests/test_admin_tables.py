from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from administration.models import AdminAuditLog


class AdminTablesTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.super_admin = User.objects.create_user(
            username="superadmin",
            email="super@example.com",
            password="pass1234",
            is_staff=True,
            is_superuser=True,
        )
        self.staff_admin = User.objects.create_user(
            username="staffadmin",
            email="staff@example.com",
            password="pass1234",
            is_staff=True,
            is_superuser=False,
        )

        for i in range(1, 21):
            User.objects.create_user(
                username=f"user{i:02d}",
                email=f"user{i:02d}@example.com",
                password="pass1234",
                is_active=(i % 2 == 0),
            )

        for i in range(1, 16):
            AdminAuditLog.objects.create(
                admin=self.super_admin,
                admin_username=self.super_admin.username,
                action="DELETE_USER" if i % 2 == 0 else "TOGGLE_USER_BLOCK",
                target_user=None,
                target_username=f"user{i:02d}",
                target_email=f"user{i:02d}@example.com",
                details={"index": i},
                request_id=f"req-{i:03d}",
            )

    def test_users_endpoint_returns_paginated_payload(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get("/api/admin/users/?page=1&page_size=10")

        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["page_size"], 10)
        self.assertGreaterEqual(response.data["count"], 22)  # 20 users + 2 admins
        self.assertEqual(len(response.data["results"]), 10)

    def test_users_endpoint_supports_filters(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get("/api/admin/users/?role=user&status=active&search=user")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["count"] > 0)
        for row in response.data["results"]:
            self.assertFalse(row["is_staff"])
            self.assertFalse(row["is_superuser"])
            self.assertTrue(row["is_active"])

    def test_staff_admin_cannot_list_other_admin_accounts(self):
        self.client.force_authenticate(user=self.staff_admin)
        response = self.client.get("/api/admin/users/?role=staff")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_audit_logs_endpoint_returns_paginated_payload_with_filters(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get("/api/admin/audit-logs/?page=1&page_size=5&action=DELETE_USER")

        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["page_size"], 5)
        self.assertTrue(response.data["count"] > 0)
        self.assertLessEqual(len(response.data["results"]), 5)
        for row in response.data["results"]:
            self.assertEqual(row["action"], "DELETE_USER")

    def test_audit_logs_endpoint_respects_timestamp_ordering(self):
        self.client.force_authenticate(user=self.super_admin)

        logs = []
        for idx in range(3):
            logs.append(
                AdminAuditLog.objects.create(
                    admin=self.super_admin,
                    admin_username=self.super_admin.username,
                    action="ORDER_TEST",
                    target_user=None,
                    target_username=f"order-user-{idx}",
                    target_email=f"order-user-{idx}@example.com",
                    details={"index": idx},
                    request_id=f"ord-test-{idx}",
                )
            )

        base = timezone.now() - timezone.timedelta(days=30)
        for idx, log in enumerate(logs):
            log.timestamp = base + timezone.timedelta(minutes=idx)
            log.save(update_fields=["timestamp"])

        oldest = self.client.get("/api/admin/audit-logs/?page=1&page_size=3&ordering=timestamp&search=ord-test-")
        newest = self.client.get("/api/admin/audit-logs/?page=1&page_size=3&ordering=-timestamp&search=ord-test-")

        self.assertEqual(oldest.status_code, 200)
        self.assertEqual(newest.status_code, 200)
        self.assertEqual(oldest.data["results"][0]["request_id"], logs[0].request_id)
        self.assertEqual(newest.data["results"][0]["request_id"], logs[2].request_id)
