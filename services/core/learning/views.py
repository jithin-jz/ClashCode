import logging
from hashlib import sha256

from celery.result import AsyncResult
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from drf_spectacular.utils import OpenApiTypes, extend_schema, inline_serializer
from rest_framework import decorators, serializers, status, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from challenges.models import Challenge, UserProgress
from challenges.serializers import ChallengeAdminSerializer, ChallengePublicSerializer
from challenges.services import ChallengeService
from challenges.execution import PistonExecutionService
from project.internal_auth import authorize_internal_request
from authentication.throttles import CodeExecutionRateThrottle
from .tasks import (
    LEADERBOARD_CACHE_KEY,
    LEADERBOARD_CACHE_TIMEOUT,
    build_leaderboard_data,
    generate_ai_analysis_task,
    generate_ai_hint_task,
)

logger = logging.getLogger(__name__)
AI_TASK_META_TIMEOUT = 60 * 60 * 24


def _analysis_cache_key(challenge_id: int, user_code: str) -> str:
    code_hash = sha256((user_code or "").encode("utf-8")).hexdigest()
    return f"ai_analysis:{challenge_id}:{code_hash}"


def _task_meta_cache_key(task_id: str) -> str:
    return f"ai_task_meta:{task_id}"


def _store_ai_task_meta(task_id: str, user_id: int, task_type: str) -> None:
    cache.set(
        _task_meta_cache_key(task_id),
        {"user_id": user_id, "task_type": task_type},
        timeout=AI_TASK_META_TIMEOUT,
    )


def _task_status_label(async_result: AsyncResult) -> str:
    if async_result.status in {"PENDING", "RECEIVED"}:
        return "queued"
    if async_result.status == "STARTED":
        return "processing"
    if async_result.status == "SUCCESS":
        return "success"
    if async_result.status in {"FAILURE", "REVOKED"}:
        return "failed"
    return async_result.status.lower()


def _build_ai_result_response(task_result: dict) -> Response:
    if not task_result or not isinstance(task_result, dict):
        return Response(
            {"error": "AI task returned invalid result"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if not task_result.get("ok"):
        return Response(
            {"error": task_result.get("error", "AI generation failed")},
            status=task_result.get("status_code", status.HTTP_503_SERVICE_UNAVAILABLE),
        )

    return Response(task_result.get("payload", {}), status=status.HTTP_200_OK)


class ChallengeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Challenge model.
    Provides standard CRUD for admins and limited views for authenticated users.
    """

    lookup_field = "slug"

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]

        # Try lookup by slug (default)
        obj = queryset.filter(slug=lookup_value).first()
        if obj:
            return obj

        if lookup_value.isdigit():
            # Try lookup by order (primary frontend use case)
            obj = queryset.filter(order=int(lookup_value)).first()
            if obj:
                return obj

            # Try lookup by ID
            obj = queryset.filter(id=int(lookup_value)).first()
            if obj:
                return obj

        # Fallback to slug (default behavior)
        from django.shortcuts import get_object_or_404
        return get_object_or_404(queryset, slug=lookup_value)

    def get_queryset(self):
        if self.request.user.is_staff:
            return Challenge.objects.all().order_by("order")
        return Challenge.objects.filter(is_published=True).order_by("order")

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return ChallengeAdminSerializer
        return ChallengePublicSerializer

    def get_permissions(self):
        """
        Permissions for different actions.
        User-facing actions require authentication.
        Management actions require staff privileges.
        Internal actions bypass DRF auth (checked via authorize_internal_request).
        """
        user_actions = [
            "list",
            "retrieve",
            "submit",
            "execute",
            "purchase_ai_assist",
            "ai_hint",
            "ai_analyze",
            "task_status",
        ]
        internal_actions = ["internal_context"]
        
        if self.action in internal_actions:
            return [AllowAny()]
        if self.action in user_actions:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    @extend_schema(
        responses={200: ChallengePublicSerializer(many=True)},
        description="List all published challenges for the user with their current progress.",
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # Use get_annotated_challenges to fetch progress for all items at once
        annotated_queryset = ChallengeService.get_annotated_challenges(request.user, queryset)
        
        data = []
        for item in annotated_queryset:
            serializer = self.get_serializer(item)
            challenge_data = serializer.data
            # Annotated fields are available on the instance
            challenge_data["status"] = getattr(item, "user_status", "LOCKED")
            challenge_data["stars"] = getattr(item, "user_stars", 0)
            data.append(challenge_data)

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={200: ChallengePublicSerializer},
        description="Retrieve details of a specific challenge including user progress and purchase status.",
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        details = ChallengeService.get_challenge_details(request.user, instance)
        data["status"] = details["status"]
        data["stars"] = details["stars"]
        data["ai_hints_purchased"] = details["ai_hints_purchased"]
        data["started_at"] = (
            details["started_at"].isoformat() if details["started_at"] else None
        )

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        request=inline_serializer(
            name="ChallengeSubmissionRequest",
            fields={
                "code": serializers.CharField(required=True),
            },
        ),
        responses={
            202: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        description="Submit code for validation. Returns a task_id for real-time result tracking.",
    )
    @decorators.action(
        detail=True, methods=["post"], throttle_classes=[CodeExecutionRateThrottle]
    )
    def submit(self, request, slug=None):
        challenge = self.get_object()
        user_code = request.data.get("code")
        if not isinstance(user_code, str) or not user_code.strip():
            return Response(
                {"status": "failed", "error": "Code is required for submission."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .tasks import submit_code_task
        task = submit_code_task.delay(request.user.id, challenge.id, user_code)
        
        return Response({
            "status": "pending",
            "task_id": task.id
        }, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        request=inline_serializer(
            name="ChallengeExecuteRequest",
            fields={
                "code": serializers.CharField(),
            },
        ),
        responses={
            202: OpenApiTypes.OBJECT,
        },
        description="Execute code server-side against challenge test cases without submitting.",
    )
    @decorators.action(
        detail=True, methods=["post"], throttle_classes=[CodeExecutionRateThrottle]
    )
    def execute(self, request, slug=None):
        challenge = self.get_object()
        user_code = request.data.get("code", "")
        
        from .tasks import execute_code_task
        task = execute_code_task.delay(request.user.id, challenge.id, user_code)
        
        return Response({
            "status": "pending",
            "task_id": task.id
        }, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        request=None,
        responses={
            200: inline_serializer(
                name="AIAssistPurchaseResponse",
                fields={
                    "status": serializers.CharField(),
                    "remaining_xp": serializers.IntegerField(),
                    "hints_purchased": serializers.IntegerField(),
                    "cost": serializers.IntegerField(),
                    "message": serializers.CharField(),
                },
            ),
            400: OpenApiTypes.OBJECT,
            402: OpenApiTypes.OBJECT,
        },
        description="Purchase the next level of AI assistance for this challenge using XP.",
    )
    @decorators.action(detail=True, methods=["post"])
    def purchase_ai_assist(self, request, slug=None):
        challenge = self.get_object()
        user = request.user
        progress, _ = UserProgress.objects.get_or_create(user=user, challenge=challenge)

        current_count = progress.ai_hints_purchased
        next_cost = 10 * (current_count + 1)
        user_xp = user.profile.xp

        try:
            remaining_xp = ChallengeService.purchase_ai_assist(request.user, challenge)
            progress.refresh_from_db()
            
            return Response(
                {
                    "status": "purchased",
                    "remaining_xp": remaining_xp,
                    "hints_purchased": progress.ai_hints_purchased,
                    "cost": next_cost,
                    "message": f"AI hint purchased! {remaining_xp} XP remaining.",
                },
                status=status.HTTP_200_OK,
            )
        except PermissionError as e:
            error_message = str(e)
            if "Maximum" in error_message:
                return Response(
                    {
                        "error": "Maximum AI hints reached",
                        "detail": "You've already purchased all 3 AI hints for this challenge.",
                        "hints_purchased": current_count,
                        "max_hints": 3,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    "error": "Insufficient XP",
                    "detail": f"You need {next_cost} XP to purchase this hint, but you only have {user_xp} XP.",
                    "required_xp": next_cost,
                    "current_xp": user_xp,
                    "shortage": next_cost - user_xp,
                    "how_to_earn": "Complete challenges to earn XP or visit the shop.",
                },
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

    @extend_schema(
        request=inline_serializer(
            name="AIHintProxyRequest",
            fields={
                "user_code": serializers.CharField(),
                "hint_level": serializers.IntegerField(),
            },
        ),
        responses={
            200: OpenApiTypes.OBJECT,
            202: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            402: OpenApiTypes.OBJECT,
            503: OpenApiTypes.OBJECT,
        },
        description="Retrieve an AI-generated hint for the challenge (Requires prior purchase of the level).",
    )
    @decorators.action(detail=True, methods=["post"], url_path="ai-hint")
    def ai_hint(self, request, slug=None):
        challenge = self.get_object()
        user = request.user
        progress, _ = UserProgress.objects.get_or_create(user=user, challenge=challenge)

        try:
            hint_level = int(request.data.get("hint_level", 1))
        except (TypeError, ValueError):
            return Response(
                {"error": "hint_level must be an integer between 1 and 3."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if hint_level < 1 or hint_level > 3:
            return Response(
                {"error": "hint_level must be between 1 and 3."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if progress.ai_hints_purchased < hint_level:
            return Response(
                {"error": f"AI Hint Level {hint_level} not purchased for this level."},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        cache_key = f"ai_hint:{user.id}:{challenge.id}:level:{hint_level}"
        cached_hint = cache.get(cache_key)
        if cached_hint is not None:
            return Response(
                {
                    "hint": cached_hint,
                    "hint_level": hint_level,
                    "max_hints": 3,
                    "cached": True,
                },
                status=status.HTTP_200_OK,
            )

        async_result = generate_ai_hint_task.delay(
            user_id=user.id,
            challenge_id=challenge.id,
            challenge_slug=challenge.slug,
            user_code=request.data.get("user_code", ""),
            hint_level=hint_level,
            user_xp=user.profile.xp,
        )
        _store_ai_task_meta(async_result.id, user.id, "hint")

        if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
            return _build_ai_result_response(async_result.result)

        return Response(
            {"task_id": async_result.id, "status": "queued"},
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        request=inline_serializer(
            name="AIAnalysisProxyRequest",
            fields={
                "user_code": serializers.CharField(),
            },
        ),
        responses={
            200: OpenApiTypes.OBJECT,
            202: OpenApiTypes.OBJECT,
            503: OpenApiTypes.OBJECT,
        },
        description="Get AI-powered analysis and feedback for your code.",
    )
    @decorators.action(detail=True, methods=["post"], url_path="ai-analyze")
    def ai_analyze(self, request, slug=None):
        challenge = self.get_object()
        user_code = request.data.get("user_code", "")
        cache_key = _analysis_cache_key(challenge.id, user_code)
        cached_analysis = cache.get(cache_key)
        if cached_analysis is not None:
            if isinstance(cached_analysis, dict):
                cached_analysis = {**cached_analysis, "cached": True}
            return Response(cached_analysis, status=status.HTTP_200_OK)

        async_result = generate_ai_analysis_task.delay(
            user_id=request.user.id,
            challenge_id=challenge.id,
            challenge_slug=challenge.slug,
            user_code=user_code,
        )
        _store_ai_task_meta(async_result.id, request.user.id, "analysis")

        if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
            return _build_ai_result_response(async_result.result)

        return Response(
            {"task_id": async_result.id, "status": "queued"},
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        responses={
            200: inline_serializer(
                name="AITaskStatusResponse",
                fields={
                    "task_id": serializers.CharField(),
                    "status": serializers.CharField(),
                    "result": serializers.JSONField(required=False),
                    "error": serializers.CharField(required=False),
                    "traceback": serializers.CharField(required=False),
                    "date_done": serializers.CharField(allow_null=True, required=False),
                },
            ),
            404: OpenApiTypes.OBJECT,
        },
        description="Poll the status of an AI hint or analysis task for the current user.",
    )
    @decorators.action(
        detail=False,
        methods=["get"],
        url_path=r"tasks/(?P<task_id>[^/.]+)/status",
    )
    def task_status(self, request, task_id=None):
        task_meta = cache.get(_task_meta_cache_key(task_id)) or {}
        if task_meta.get("user_id") != request.user.id:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        async_result = AsyncResult(task_id)
        response_data = {
            "task_id": task_id,
            "status": _task_status_label(async_result),
            "date_done": (
                str(async_result.date_done) if async_result.date_done else None
            ),
        }

        if not async_result.ready():
            return Response(response_data, status=status.HTTP_200_OK)

        task_result = async_result.result
        if (
            async_result.successful()
            and isinstance(task_result, dict)
            and task_result.get("ok")
        ):
            response_data["result"] = task_result.get("payload", {})
            return Response(response_data, status=status.HTTP_200_OK)

        if async_result.successful() and isinstance(task_result, dict):
            response_data["error"] = task_result.get("error", "AI task failed")
            return Response(response_data, status=status.HTTP_200_OK)

        response_data["error"] = str(task_result)
        response_data["traceback"] = async_result.traceback
        return Response(response_data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: inline_serializer(
                name="ChallengeContextResponse",
                fields={
                    "challenge_title": serializers.CharField(),
                    "description": serializers.CharField(),
                    "initial_code": serializers.CharField(),
                    "test_code": serializers.CharField(),
                },
            ),
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        description="Internal endpoint to fetch full challenge context (Requires INTERNAL_API_KEY).",
    )
    @decorators.action(detail=True, methods=["get"], url_path="context")
    def internal_context(self, request, slug=None):
        if not authorize_internal_request(request):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            challenge = Challenge.objects.get(slug=slug)
            return Response(
                {
                    "challenge_title": challenge.title,
                    "challenge_description": challenge.description,
                    "description": challenge.description,
                    "initial_code": challenge.initial_code,
                    "test_code": challenge.test_code,
                },
                status=status.HTTP_200_OK,
            )
        except Challenge.DoesNotExist:
            return Response(
                {"error": "Challenge not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception:
            return Response(
                {"error": "Internal error fetching context"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LeaderboardView(APIView):
    """
    View to retrieve the global user leaderboard.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: inline_serializer(
                name="LeaderboardEntry",
                fields={
                    "username": serializers.CharField(),
                    "avatar": serializers.URLField(allow_null=True),
                    "completed_levels": serializers.IntegerField(),
                    "xp": serializers.IntegerField(),
                },
                many=True,
            )
        },
        description="Get global leaderboard data (limited to top 100 users, cached and refreshed by the backend worker).",
    )
    def get(self, request):
        cached_data = cache.get(LEADERBOARD_CACHE_KEY)
        if cached_data is not None:
            return Response(cached_data, status=status.HTTP_200_OK)

        data = build_leaderboard_data()
        cache.set(LEADERBOARD_CACHE_KEY, data, timeout=LEADERBOARD_CACHE_TIMEOUT)
        return Response(data, status=status.HTTP_200_OK)
