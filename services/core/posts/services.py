import logging

from django.db.models import BooleanField, Count, Exists, OuterRef, Value

from .models import Post

logger = logging.getLogger(__name__)


class PostService:
    """
    Business logic for managing posts, likes, and interactions.
    """

    @staticmethod
    def toggle_like(post, user):
        """
        Toggles a user's like on a post.
        Returns (is_liked, likes_count).
        """
        like_exists = post.likes.filter(id=user.id).exists()

        if like_exists:
            post.likes.remove(user)
            is_liked = False
        else:
            post.likes.add(user)
            is_liked = True

        return is_liked, post.likes.count()

    @staticmethod
    def get_annotated_posts(queryset, user=None):
        """
        Annotates a post queryset with likes_count and is_liked status.
        """
        queryset = queryset.annotate(likes_count=Count("likes", distinct=True))

        if user and user.is_authenticated:
            like_exists = Post.likes.through.objects.filter(post_id=OuterRef("pk"), user_id=user.id)
            queryset = queryset.annotate(is_liked=Exists(like_exists))
        else:
            queryset = queryset.annotate(is_liked=Value(False, output_field=BooleanField()))

        return queryset

    @staticmethod
    def create_post(user, image, caption=""):
        """Creates a new post for a user."""
        return Post.objects.create(user=user, image=image, caption=caption)
