from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from project.health import HealthCheckView
from project.views import ServiceIndexView, TaskResultsListView, TaskStatusView

admin.site.site_header = "CLASHCODE Admin Portal"
admin.site.site_title = "CLASHCODE Admin"
admin.site.index_title = "Welcome to CLASHCODE Admin Portal"

urlpatterns = [
    # Flower Redirect
    path("admin/flower/", RedirectView.as_view(url="http://localhost:5555"), name="admin-flower"),
    # Health check
    path("", ServiceIndexView.as_view(), name="service-index"),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("authentication.urls")),
    path("api/rewards/", include("rewards.urls")),
    path("api/profiles/", include("users.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/store/", include("store.urls")),
    path("api/admin/", include("administration.urls")),
    path("api/", include("learning.urls")),
    path("api/", include("certificates.urls")),
    path("api/posts/", include("posts.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/achievements/", include("achievements.urls")),
    path("api/xpoint/", include("xpoint.urls")),
    # Celery task result endpoints (admin only)
    path("api/tasks/<str:task_id>/status/", TaskStatusView.as_view(), name="task-status"),
    path("api/tasks/results/", TaskResultsListView.as_view(), name="task-results"),
    # Swagger Documentation routes
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
