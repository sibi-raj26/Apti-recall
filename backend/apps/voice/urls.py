from django.urls import path
from . import views

urlpatterns = [
    path("generate/", views.GenerateTTSView.as_view(), name="voice-generate"),
    path("<int:pk>/", views.VoiceDetailView.as_view(), name="voice-detail"),
    path("<int:pk>/regenerate/", views.RegenerateTTSView.as_view(), name="voice-regenerate"),
]
