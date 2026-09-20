from django.urls import path
from . import views


urlpatterns = [
    # Your endpoints go here
    path("", views.FeedbackCreateView.as_view(), name="feedback-create"),
    path("my/", views.MyFeedbackListView.as_view(), name="feedback-my"),
    path("eligible-sessions/", views.EligibleSessionsView.as_view(), name="feedback-eligible-sessions"),
    path("instructor-summary/", views.InstructorSummaryView.as_view(), name="feedback-instructor-summary"),
]
