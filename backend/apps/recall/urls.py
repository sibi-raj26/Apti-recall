from django.urls import path
from . import views

urlpatterns = [
    path("schedule/", views.RecallScheduleView.as_view(), name="recall-schedule"),
    path("submit/", views.RecallSubmitView.as_view(), name="recall-submit"),
    path("weak-topics/", views.WeakTopicsView.as_view(), name="recall-weak-topics"),
    path("analytics/", views.RecallAnalyticsView.as_view(), name="recall-analytics"),
]
