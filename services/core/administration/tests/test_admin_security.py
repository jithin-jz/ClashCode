from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from administration.models import AdminAuditLog


class AdminSecurityTest(TestCase):
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
        self.regular_user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="pass1234",
        )
        self.other_staff = User.objects.create_user(
            username="otherstaff",
            email="otherstaff@example.com",
            password="pass1234",
            is_staff=True,
            is_superuser=False,
        )

    def test_staff_cannot_block_superuser(self):
        self.client.force_authenticate(user=self.staff_admin)
        response = self.client.post(
            f"/api/admin/users/{self.super_admin.username}/toggle-block/",
            {"reason": "policy violation"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("Only superusers", response.data["error"])

    def test_staff_can_block_regular_user_and_audit_is_recorded(self):
        self.client.force_authenticate(user=self.staff_admin)
        response = self.client.post(
            f"/api/admin/users/{self.regular_user.username}/toggle-block/",
            {"reason": "spam"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)

        audit = AdminAuditLog.objects.filter(action="BLOCK_USER").latest(
            "timestamp"
        )
        self.assertEqual(audit.admin_username, self.staff_admin.username)
        self.assertEqual(audit.target_username, self.regular_user.username)
        self.assertEqual(audit.target_email, self.regular_user.email)
        self.assertEqual(audit.details.get("reason"), "spam")
        self.assertTrue(bool(audit.request_id))

    def test_staff_cannot_delete_staff_user(self):
        self.client.force_authenticate(user=self.staff_admin)
        response = self.client.delete(
            f"/api/admin/users/{self.other_staff.username}/delete/"
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("Only superusers", response.data["error"])

    def test_superuser_delete_keeps_audit_snapshot(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.delete(
            f"/api/admin/users/{self.regular_user.username}/delete/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            User.objects.filter(username=self.regular_user.username).exists()
        )

        audit = AdminAuditLog.objects.filter(action="SOFT_DELETE_USER").latest("timestamp")
        self.assertEqual(audit.admin_username, self.super_admin.username)
        self.assertEqual(audit.target_username, "regularuser")
        self.assertEqual(audit.target_email, "regular@example.com")
        self.assertIsNone(audit.target_user)
