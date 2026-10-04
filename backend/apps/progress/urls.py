from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="progress-dashboard"),
    path("accuracy/", views.AccuracyView.as_view(), name="progress-accuracy"),
    path("topics/", views.TopicBreakdownView.as_view(), name="progress-topics"),
    path("mistakes/", views.RecentMistakesView.as_view(), name="progress-mistakes"),
]
