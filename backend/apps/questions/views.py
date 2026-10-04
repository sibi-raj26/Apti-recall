from rest_framework import views, response, status, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import Question, SolutionStep, Shortcut, UploadedQuestion
from .serializers import QuestionListSerializer, QuestionDetailSerializer, UploadedQuestionSerializer, SolutionStepSerializer, ShortcutSerializer
from .filters import QuestionFilter


class QuestionListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = QuestionFilter
    ordering_fields = ["created_at", "difficulty", "topic__name"]
    ordering = ["-created_at"]
    page_size = 20

    def get(self, request):
        queryset = Question.objects.filter(is_active=True)
        filtered = DjangoFilterBackend().filter_queryset(request, queryset, self)
        ordered = filters.OrderingFilter().filter_queryset(request, filtered, self)
        page = self._paginate(ordered)
        if page is not None:
            serializer = QuestionListSerializer(page, many=True)
            return self._paginated_response(serializer.data)
        serializer = QuestionListSerializer(ordered, many=True)
        return response.Response({"success": True, "data": serializer.data})

    def _paginate(self, queryset):
        page_size = self.page_size
        page = self.request.query_params.get("page", 1)
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1
        start = (page - 1) * page_size
        end = start + page_size
        if start >= queryset.count():
            return queryset.none()
        return queryset[start:end]

    def _paginated_response(self, data):
        page_size = self.page_size
        page = self.request.query_params.get("page", 1)
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1
        queryset = Question.objects.filter(is_active=True)
        total = queryset.count()
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        return response.Response({
            "success": True,
            "data": data,
            "meta": {
                "page": page,
                "total_pages": total_pages,
                "total_count": total,
            }
        })

    page_size = 20


class QuestionDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk):
        try:
            question = Question.objects.get(pk=pk, is_active=True)
        except Question.DoesNotExist:
            return response.Response({"success": False, "error": {"code": "NOT_FOUND", "message": "Question not found"}}, status=status.HTTP_404_NOT_FOUND)
        serializer = QuestionDetailSerializer(question)
        return response.Response({"success": True, "data": serializer.data})


class QuestionSolutionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk):
        try:
            question = Question.objects.get(pk=pk, is_active=True)
        except Question.DoesNotExist:
            return response.Response({"success": False, "error": {"code": "NOT_FOUND", "message": "Question not found"}}, status=status.HTTP_404_NOT_FOUND)
        steps = question.solution_steps.all().order_by("step_number")
        serializer = SolutionStepSerializer(steps, many=True)
        return response.Response({"success": True, "data": serializer.data})


class QuestionShortcutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk):
        try:
            question = Question.objects.get(pk=pk, is_active=True)
        except Question.DoesNotExist:
            return response.Response({"success": False, "error": {"code": "NOT_FOUND", "message": "Question not found"}}, status=status.HTTP_404_NOT_FOUND)
        shortcuts = question.shortcuts.all().order_by("title")
        serializer = ShortcutSerializer(shortcuts, many=True)
        return response.Response({"success": True, "data": serializer.data})


class QuestionAttemptView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        return response.Response({"detail": "Not implemented in Phase 2."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class QuestionSimilarView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk):
        return response.Response({"detail": "Not implemented in Phase 2."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class QuestionHintView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        return response.Response({"detail": "Not implemented in Phase 2."}, status=status.HTTP_501_NOT_IMPLEMENTED)
