from django.urls import path
from . import views

urlpatterns = [
    path("", views.QuestionListView.as_view(), name="question-list"),
    path("<int:pk>/", views.QuestionDetailView.as_view(), name="question-detail"),
    path("<int:pk>/solution/", views.QuestionSolutionView.as_view(), name="question-solution"),
    path("<int:pk>/shortcut/", views.QuestionShortcutView.as_view(), name="question-shortcut"),
    path("<int:pk>/attempt/", views.QuestionAttemptView.as_view(), name="question-attempt"),
    path("<int:pk>/similar/", views.QuestionSimilarView.as_view(), name="question-similar"),
    path("<int:pk>/hint/", views.QuestionHintView.as_view(), name="question-hint"),
]
