from rest_framework import views, response, status


class DashboardView(views.APIView):
    def get(self, request):
        return response.Response(
            {"detail": "Not implemented in Phase 11."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class AccuracyView(views.APIView):
    def get(self, request):
        return response.Response(
            {"detail": "Not implemented in Phase 11."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class TopicBreakdownView(views.APIView):
    def get(self, request):
        return response.Response(
            {"detail": "Not implemented in Phase 11."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class RecentMistakesView(views.APIView):
    def get(self, request):
        return response.Response(
            {"detail": "Not implemented in Phase 11."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
