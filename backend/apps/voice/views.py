from rest_framework import views, response, status


class GenerateTTSView(views.APIView):
    def post(self, request):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class VoiceDetailView(views.APIView):
    def get(self, request, pk):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class RegenerateTTSView(views.APIView):
    def post(self, request, pk):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)
