from django.urls import path
from . import views

urlpatterns = [
    path("text/", views.SolveTextView.as_view(), name="solve-text"),
    path("verify/", views.VerifyAnswerView.as_view(), name="solve-verify"),
    path("history/", views.SolveHistoryView.as_view(), name="solve-history"),
]
