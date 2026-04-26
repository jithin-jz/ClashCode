from django.urls import path

from .views import CheckInView

app_name = "rewards"

urlpatterns = [
    path("check-in/", CheckInView.as_view(), name="check-in"),
]
