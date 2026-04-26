from django.urls import path

from .views import (
    ContributionHistoryView,
    CurrentUserView,
    FollowToggleView,
    MediaUploadView,
    ProfileDetailView,
    ProfileUpdateView,
    RedeemReferralView,
    SuggestedUsersView,
    UserFollowersView,
    UserFollowingView,
)

urlpatterns = [
    path("user/", CurrentUserView.as_view(), name="get_current_user"),
    path("user/update/", ProfileUpdateView.as_view(), name="update_profile"),
    path("user/redeem-referral/", RedeemReferralView.as_view(), name="redeem_referral"),
    path("users/suggestions/", SuggestedUsersView.as_view(), name="suggested_users"),
    path(
        "users/<str:username>/stats/contributions/",
        ContributionHistoryView.as_view(),
        name="user_contributions",
    ),
    path("users/<str:username>/", ProfileDetailView.as_view(), name="profile_detail"),
    path("users/<str:username>/follow/", FollowToggleView.as_view(), name="toggle_follow"),
    path(
        "users/<str:username>/followers/",
        UserFollowersView.as_view(),
        name="user_followers",
    ),
    path(
        "users/<str:username>/following/",
        UserFollowingView.as_view(),
        name="user_following",
    ),
    path("media/upload/", MediaUploadView.as_view(), name="media_upload"),
]
