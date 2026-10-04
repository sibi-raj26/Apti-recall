from django.urls import path
from . import views

urlpatterns = [
    path("next/", views.PracticeNextView.as_view(), name="practice-next"),
    path("<int:pk>/submit/", views.PracticeSubmitView.as_view(), name="practice-submit"),
    path("history/", views.PracticeHistoryView.as_view(), name="practice-history"),
    path("generate/", views.PracticeGenerateView.as_view(), name="practice-generate"),
]
