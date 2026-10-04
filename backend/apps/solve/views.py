import logging

from rest_framework import views, response, status, permissions

from backend.apps.solve.services.solver_service import SolveService
from backend.apps.solve.services.verification_service import VerificationService
from backend.apps.solve.serializers import SolveRequestSerializer, SolveResponseSerializer, VerifyRequestSerializer, VerifyResponseSerializer
from backend.apps.solve.models import UserAttempt, VerificationRecord

logger = logging.getLogger(__name__)


class SolveTextView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SolveRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response({"success": False, "error": {"code": "VALIDATION_ERROR", "message": serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)

        question_text = serializer.validated_data["question_text"]
        try:
            service = SolveService()
            result = service.solve(request.user, question_text)
        except ValueError as exc:
            return response.Response({"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            logger.warning("AI solver runtime error: %s", exc)
            return response.Response({"success": False, "error": {"code": "AI_UNAVAILABLE", "message": "AI solver is temporarily unavailable."}}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as exc:
            logger.exception("Unexpected solve error")
            return response.Response({"success": False, "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        output_serializer = SolveResponseSerializer(result)
        return response.Response({"success": True, "data": output_serializer.data})


class SolveHistoryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    page_size = 20

    def get(self, request):
        page = self._get_page()
        queryset = UserAttempt.objects.filter(user=request.user).order_by("-created_at")
        total = queryset.count()
        start = (page - 1) * self.page_size
        end = start + self.page_size
        attempts = queryset[start:end]
        from backend.apps.solve.serializers import UserAttemptSerializer
        serializer = UserAttemptSerializer(attempts, many=True)
        total_pages = (total + self.page_size - 1) // self.page_size if total > 0 else 1
        return response.Response({
            "success": True,
            "data": serializer.data,
            "meta": {
                "page": page,
                "total_pages": total_pages,
                "total_count": total,
            }
        })

    def _get_page(self):
        page = self.request.query_params.get("page", 1)
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1
        return max(1, page)


class VerifyAnswerView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = VerifyRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response({"success": False, "error": {"code": "VALIDATION_ERROR", "message": serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)

        attempt_id = serializer.validated_data["attempt_id"]
        try:
            attempt = UserAttempt.objects.get(pk=attempt_id)
        except UserAttempt.DoesNotExist:
            return response.Response({"success": False, "error": {"code": "NOT_FOUND", "message": "Attempt not found."}}, status=status.HTTP_404_NOT_FOUND)

        if attempt.user_id != request.user.id:
            return response.Response({"success": False, "error": {"code": "FORBIDDEN", "message": "You do not own this attempt."}}, status=status.HTTP_403_FORBIDDEN)

        solve_output = attempt.solution_feedback or {}
        try:
            service = VerificationService()
            result = service.verify(attempt, solve_output)
        except Exception as exc:
            logger.exception("Verification error for attempt %s", attempt_id)
            return response.Response({"success": False, "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred during verification."}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        verification = VerificationRecord.objects.filter(attempt=attempt).order_by("-created_at").first()
        data = {
            "attempt_id": attempt.id,
            "status": result.status,
            "method": result.method,
            "confidence": result.confidence,
            "details": result.details,
            "checks": result.checks,
            "expected": result.expected,
            "actual": result.actual,
        }
        attempt.solution_feedback = attempt.solution_feedback or {}
        attempt.solution_feedback["verification_status"] = result.status
        attempt.solution_feedback["verification_details"] = {
            "method": result.method,
            "confidence": result.confidence,
            "details": result.details,
            "checks": result.checks,
            "expected": result.expected,
            "actual": result.actual,
        }
        attempt.save(update_fields=["solution_feedback"])
        output_serializer = VerifyResponseSerializer(instance=data)
        return response.Response({"success": True, "data": output_serializer.data})
