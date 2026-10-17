import io

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from project.validators import validate_image_upload


def _png(size=(10, 10)) -> SimpleUploadedFile:
    buffer = io.BytesIO()
    Image.new("RGB", size, (0, 128, 255)).save(buffer, "PNG")
    return SimpleUploadedFile("ok.png", buffer.getvalue(), content_type="image/png")


class ImageValidatorTests(TestCase):
    def test_accepts_real_image(self):
        validate_image_upload(_png())

    def test_rejects_html_disguised_as_image(self):
        fake = SimpleUploadedFile("avatar.jpg", b"<script>alert(1)</script>", content_type="image/jpeg")
        with self.assertRaises(ValidationError):
            validate_image_upload(fake)

    def test_rejects_svg(self):
        svg = SimpleUploadedFile("a.svg", b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>')
        with self.assertRaises(ValidationError):
            validate_image_upload(svg)

    @override_settings(MAX_IMAGE_UPLOAD_BYTES=100)
    def test_rejects_oversized_image(self):
        with self.assertRaises(ValidationError):
            validate_image_upload(_png((200, 200)))


class ProfileUploadTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="uploader", email="u@example.com", password="pw")
        self.client.force_authenticate(user=self.user)

    def test_profile_rejects_non_image_avatar(self):
        fake = SimpleUploadedFile("avatar.png", b"not an image", content_type="image/png")
        response = self.client.patch("/api/profiles/user/update/", {"avatar": fake}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.avatar)
