from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import Post
from .permissions import IsOwnerOrReadOnly
from .serializers import PostLikeResponseSerializer, PostSerializer
from .services import PostService


class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing posts.
    """

    queryset = Post.objects.all().select_related("user", "user__profile")
    serializer_class = PostSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Optimized queryset with service-layer annotations."""
        queryset = super().get_queryset()
        queryset = PostService.get_annotated_posts(queryset, user=self.request.user)

        username = self.request.query_params.get("username")
        if username:
            queryset = queryset.filter(user__username=username)

        return queryset

    def perform_create(self, serializer):
        """Save post with the authenticated user."""
        serializer.save(user=self.request.user)

    @extend_schema(
        request=None,
        responses={200: PostLikeResponseSerializer},
        description="Toggle like/unlike on a specific post.",
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        """Action to like or unlike a post via PostService."""
        post = self.get_object()
        is_liked, likes_count = PostService.toggle_like(post, request.user)

        return Response(
            {"is_liked": is_liked, "likes_count": likes_count},
            status=status.HTTP_200_OK,
        )
