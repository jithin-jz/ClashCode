import io

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from posts.models import Post


class PostViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="author", password="password")
        self.other_user = User.objects.create_user(username="stranger", password="password")
        self.client.force_authenticate(user=self.user)

        # Helper to create a dummy image
        file_obj = io.BytesIO()
        image = Image.new("RGB", (100, 100), (255, 0, 0))
        image.save(file_obj, "jpeg")
        file_obj.seek(0)
        self.dummy_image = SimpleUploadedFile("test.jpg", file_obj.read(), content_type="image/jpeg")

    def test_create_post(self):
        url = reverse("post-list")
        data = {"caption": "Test post", "image": self.dummy_image}
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.first().user, self.user)

    def test_list_posts(self):
        Post.objects.create(user=self.user, caption="P1", image=self.dummy_image)
        Post.objects.create(user=self.other_user, caption="P2", image=self.dummy_image)

        url = reverse("post-list")
        self.client.force_authenticate(user=None)  # Publicly readable
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_username(self):
        Post.objects.create(user=self.user, caption="Author Post", image=self.dummy_image)
        Post.objects.create(user=self.other_user, caption="Stranger Post", image=self.dummy_image)

        url = reverse("post-list")
        response = self.client.get(url, {"username": "author"})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["user"]["username"], "author")

    def test_like_action(self):
        post = Post.objects.create(user=self.other_user, caption="Like me", image=self.dummy_image)
        url = reverse("post-like", kwargs={"pk": post.id})

        # Like
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_liked"])
        self.assertEqual(response.data["likes_count"], 1)

        # Unlike
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_liked"])
        self.assertEqual(response.data["likes_count"], 0)

    def test_edit_delete_permissions(self):
        post = Post.objects.create(user=self.user, caption="Mine", image=self.dummy_image)
        url = reverse("post-detail", kwargs={"pk": post.id})

        # stranger tries to edit
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(url, {"caption": "Edited by stranger"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # owner edits
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(url, {"caption": "Edited by me"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # owner deletes
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)
