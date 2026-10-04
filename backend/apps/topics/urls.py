from django.urls import path
from . import views

urlpatterns = [
    path("", views.TopicListView.as_view(), name="topic-list"),
    path("<int:pk>/", views.TopicDetailView.as_view(), name="topic-detail"),
    path("<int:pk>/subtopics/", views.TopicSubtopicsView.as_view(), name="topic-subtopics"),
    path("<int:pk>/problem-types/", views.TopicProblemTypesView.as_view(), name="topic-problem-types"),
    path("<int:pk>/formulas/", views.TopicFormulasView.as_view(), name="topic-formulas"),
]
