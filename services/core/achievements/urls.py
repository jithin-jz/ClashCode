from django.urls import path

from . import views

urlpatterns = [
    path("", views.AchievementListView.as_view(), name="achievement-list"),
    path(
        "user/<str:username>/",
        views.UserAchievementListView.as_view(),
        name="user-achievements",
    ),
]
