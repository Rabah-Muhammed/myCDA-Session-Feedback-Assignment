from django.urls import path
from . import views

urlpatterns = [
    path("", views.ClassListView.as_view(), name="class-list"),
    path(
        "<int:class_id>/sessions/",
        views.SessionListView.as_view(),
        name="session-list",
    ),
    path(
        "enrollments/",
        views.MyEnrollmentsView.as_view(),
        name="my-enrollments",
    ),
]
