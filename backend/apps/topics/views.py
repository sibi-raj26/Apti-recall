from rest_framework import views, response, status, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import Topic, Subtopic, ProblemType, Formula
from .serializers import TopicListSerializer, TopicDetailSerializer, SubtopicSerializer, ProblemTypeSerializer, FormulaSerializer
from .filters import TopicFilter


class TopicListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = TopicFilter
    ordering_fields = ["order", "name", "created_at"]
    ordering = ["order", "name"]
    page_size = 20

    def get(self, request):
        is_active_param = request.query_params.get("is_active")
        if is_active_param is not None:
            is_active_val = is_active_param.lower() in ("true", "1", "yes")
            queryset = Topic.objects.filter(is_active=is_active_val)
        else:
            queryset = Topic.objects.filter(is_active=True)
        filtered = DjangoFilterBackend().filter_queryset(request, queryset, self)
        ordered = filters.OrderingFilter().filter_queryset(request, filtered, self)
        page = self._paginate(ordered)
        if page is not None:
            serializer = TopicListSerializer(page, many=True)
            return self._paginated_response(serializer.data)
        serializer = TopicListSerializer(ordered, many=True)
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
        is_active_param = self.request.query_params.get("is_active")
        if is_active_param is not None:
            is_active_val = is_active_param.lower() in ("true", "1", "yes")
            queryset = Topic.objects.filter(is_active=is_active_val)
        else:
            queryset = Topic.objects.filter(is_active=True)
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


class TopicDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk):
        try:
            topic = Topic.objects.get(pk=pk, is_active=True)
        except Topic.DoesNotExist:
            return response.Response({"success": False, "error": {"code": "NOT_FOUND", "message": "Topic not found"}}, status=status.HTTP_404_NOT_FOUND)
        serializer = TopicDetailSerializer(topic)
        return response.Response({"success": True, "data": serializer.data})


class TopicSubtopicsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk):
        try:
            topic = Topic.objects.get(pk=pk, is_active=True)
        except Topic.DoesNotExist:
            return response.Response({"success": False, "error": {"code": "NOT_FOUND", "message": "Topic not found"}}, status=status.HTTP_404_NOT_FOUND)
        subtopics = topic.subtopics.all().order_by("order", "name")
        serializer = SubtopicSerializer(subtopics, many=True)
        return response.Response({"success": True, "data": serializer.data})


class TopicProblemTypesView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk):
        try:
            topic = Topic.objects.get(pk=pk, is_active=True)
        except Topic.DoesNotExist:
            return response.Response({"success": False, "error": {"code": "NOT_FOUND", "message": "Topic not found"}}, status=status.HTTP_404_NOT_FOUND)
        problem_types = topic.problem_types.filter(is_active=True).order_by("name")
        serializer = ProblemTypeSerializer(problem_types, many=True)
        return response.Response({"success": True, "data": serializer.data})


class TopicFormulasView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk):
        try:
            topic = Topic.objects.get(pk=pk, is_active=True)
        except Topic.DoesNotExist:
            return response.Response({"success": False, "error": {"code": "NOT_FOUND", "message": "Topic not found"}}, status=status.HTTP_404_NOT_FOUND)
        formulas = topic.formulas.all().order_by("name")
        serializer = FormulaSerializer(formulas, many=True)
        return response.Response({"success": True, "data": serializer.data})
