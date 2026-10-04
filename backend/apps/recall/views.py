import logging

from rest_framework import views, response, status, permissions

from backend.apps.recall.serializers import RecallRecordSerializer
from backend.apps.recall.services.recall_service import get_daily_queue, get_weak_topics, get_recall_analytics
from backend.apps.solve.models import UserAttempt

logger = logging.getLogger(__name__)


class RecallScheduleView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        records = get_daily_queue(request.user)
        serializer = RecallRecordSerializer(records, many=True)
        return response.Response({"success": True, "data": serializer.data})


class RecallSubmitView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        attempt_id = request.data.get("attempt_id")
        if not attempt_id:
            return response.Response({"success": False, "error": {"code": "VALIDATION_ERROR", "message": "attempt_id is required."}}, status=status.HTTP_400_BAD_REQUEST)

        try:
            attempt = request.user.attempts.get(pk=attempt_id, status="completed")
        except UserAttempt.DoesNotExist:
            return response.Response({"success": False, "error": {"code": "NOT_FOUND", "message": "Completed attempt not found."}}, status=status.HTTP_404_NOT_FOUND)

        try:
            from backend.apps.recall.services.recall_service import update_recall
            record = update_recall(request.user, attempt)
            serializer = RecallRecordSerializer(record)
            return response.Response({"success": True, "data": serializer.data})
        except ValueError as exc:
            return response.Response({"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Recall update failed")
            return response.Response({"success": False, "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WeakTopicsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        records = get_weak_topics(request.user)
        serializer = RecallRecordSerializer(records, many=True)
        return response.Response({"success": True, "data": serializer.data})


class RecallAnalyticsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        analytics = get_recall_analytics(request.user)
        return response.Response({"success": True, "data": analytics})
