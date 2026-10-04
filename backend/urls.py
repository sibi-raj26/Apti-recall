from django.conf import settings
from django.urls import include, path
from django.http import JsonResponse


def health(request):
    return JsonResponse({
        "status": "ok",
        "service": "AptiRecall API",
    })


urlpatterns = [
    path("api/health/", health, name="health"),
    path("api/auth/", include("backend.apps.users.urls")),
    path("api/topics/", include("backend.apps.topics.urls")),
    path("api/questions/", include("backend.apps.questions.urls")),
    path("api/solve/", include("backend.apps.solve.urls")),
    path("api/upload/", include("backend.apps.upload.urls")),
    path("api/recall/", include("backend.apps.recall.urls")),
    path("api/practice/", include("backend.apps.practice.urls")),
    path("api/progress/", include("backend.apps.progress.urls")),
    path("api/voice/", include("backend.apps.voice.urls")),
    path("api/admin-panel/", include("backend.apps.admin_panel.urls")),
]
