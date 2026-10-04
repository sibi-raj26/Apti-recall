from rest_framework import views, response, status


class AdminDashboardView(views.APIView):
    def get(self, request):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class AdminTopicListView(views.APIView):
    def get(self, request):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class AdminTopicDetailView(views.APIView):
    def get(self, request, pk):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request, pk):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class AdminQuestionListView(views.APIView):
    def get(self, request):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class AdminQuestionDetailView(views.APIView):
    def get(self, request, pk):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request, pk):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class AdminBulkImportView(views.APIView):
    def post(self, request):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class AdminUserListView(views.APIView):
    def get(self, request):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class AdminPerformanceView(views.APIView):
    def get(self, request):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)
