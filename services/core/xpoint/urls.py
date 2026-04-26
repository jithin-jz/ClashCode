from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import XPViewSet

router = DefaultRouter()
router.register(r"history", XPViewSet, basename="xp")

urlpatterns = [
    path("", include(router.urls)),
]
