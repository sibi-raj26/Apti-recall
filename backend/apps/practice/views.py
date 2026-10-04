import logging

from rest_framework import views, response, status, permissions

from backend.apps.practice.serializers import PracticeGenerateSerializer
from backend.apps.practice.services.practice_service import PracticeService
from backend.apps.questions.models import Question, UploadedQuestion

logger = logging.getLogger(__name__)


class PracticeNextView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class PracticeSubmitView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class PracticeHistoryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return response.Response({"detail": "Not implemented in Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class PracticeGenerateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PracticeGenerateSerializer

    def post(self, request):
        serializer = PracticeGenerateSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response({"success": False, "error": {"code": "VALIDATION_ERROR", "message": serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            source_question = None
            upload = None
            question_index = None
            topic = data.get("topic")
            problem_type = data.get("problem_type")
            difficulty = data.get("difficulty", "easy")
            question_text = data.get("question_text")
            concept = data.get("concept")
            approach = data.get("approach")

            if data.get("question_id") is not None:
                try:
                    source_question = Question.objects.get(pk=data["question_id"], is_active=True)
                except Question.DoesNotExist:
                    return response.Response({"success": False, "error": {"code": "NOT_FOUND", "message": "Question not found."}}, status=status.HTTP_404_NOT_FOUND)
                topic = source_question.topic.name
                problem_type = source_question.problem_type.name
                difficulty = source_question.difficulty
                question_text = source_question.question_text
                concept = source_question.explanation_concept
                approach = source_question.explanation_approach

            elif data.get("upload_id") is not None:
                try:
                    upload = UploadedQuestion.objects.get(pk=data["upload_id"], user=request.user)
                except UploadedQuestion.DoesNotExist:
                    return response.Response({"success": False, "error": {"code": "NOT_FOUND", "message": "Upload not found."}}, status=status.HTTP_404_NOT_FOUND)
                if upload.status != "ocr_completed":
                    return response.Response({"success": False, "error": {"code": "OCR_NOT_READY", "message": "OCR processing has not completed for this upload."}}, status=status.HTTP_400_BAD_REQUEST)
                question_index = data.get("question_index", 1)

            service = PracticeService()
            result = service.generate_similar_question(
                user=request.user,
                source_question=source_question,
                upload=upload,
                question_index=question_index,
                topic=topic,
                problem_type=problem_type,
                difficulty=difficulty,
                question_text=question_text,
                concept=concept,
                approach=approach,
            )
            return response.Response({"success": True, "data": result}, status=status.HTTP_200_OK)

        except ValueError as exc:
            return response.Response({"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            logger.warning("Practice generation AI runtime error: %s", exc)
            return response.Response({"success": False, "error": {"code": "AI_UNAVAILABLE", "message": "AI service is temporarily unavailable."}}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as exc:
            logger.exception("Unexpected practice generation error")
            return response.Response({"success": False, "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
