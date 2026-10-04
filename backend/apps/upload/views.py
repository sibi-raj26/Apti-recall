import logging
import os
import uuid
from typing import Optional

from django.conf import settings
from django.utils import timezone
from rest_framework import views, response, status, permissions

from backend.apps.questions.models import UploadedQuestion
from backend.apps.upload.serializers import UploadQuestionSerializer, UploadedQuestionSerializer, UploadResultSerializer, UploadSolveSerializer
from backend.apps.upload.services.image_preprocessor import ImagePreprocessor
from backend.apps.upload.services.question_extractor import QuestionExtractor
from backend.ai_services.ocr.base import OCRResult
from backend.ai_services.ocr.service import OCRService
from backend.apps.solve.services.solver_service import SolveService

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


class UploadImageView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UploadQuestionSerializer

    def post(self, request):
        serializer = UploadQuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response({"success": False, "error": {"code": "VALIDATION_ERROR", "message": serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)

        image_file = serializer.validated_data["image"]
        try:
            self._validate_file(image_file)
            uploaded = self._create_uploaded_question(request.user, image_file)
            self._process_upload(uploaded, image_file)
            result_data = self._build_response(uploaded)
            return response.Response({"success": True, "data": result_data}, status=status.HTTP_200_OK)
        except ValueError as exc:
            return response.Response({"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Unexpected upload error")
            return response.Response({"success": False, "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _validate_file(self, image_file):
        max_size = getattr(settings, "MAX_UPLOAD_SIZE", 10 * 1024 * 1024)
        if image_file.size > max_size:
            raise ValueError(f"File size exceeds {max_size / 1024 / 1024}MB limit.")
        extension = self._get_extension(image_file.name)
        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: .{extension}")
        content_type = getattr(image_file, "content_type", "") or ""
        if not content_type.startswith("image/"):
            raise ValueError("Unsupported file content type.")
        self._validate_file_magic(image_file, extension)

    def _get_extension(self, filename: str) -> str:
        _, ext = os.path.splitext(filename)
        return ext.lower().lstrip(".")

    def _validate_file_magic(self, image_file, extension: str):
        magic_map = {
            "jpg": [b"\xff\xd8\xff"],
            "jpeg": [b"\xff\xd8\xff"],
            "png": [b"\x89PNG\r\n\x1a\n"],
            "webp": [b"RIFF"],
        }
        expected_magic = magic_map.get(extension, [])
        if not expected_magic:
            return
        image_file.seek(0)
        header = image_file.read(12)
        image_file.seek(0)
        for magic in expected_magic:
            if header.startswith(magic):
                return
        raise ValueError("File content does not match the expected image format.")

    def _create_uploaded_question(self, user, image_file) -> UploadedQuestion:
        safe_name = self._safe_filename(image_file.name)
        upload = UploadedQuestion(user=user, status="processing")
        upload.image.save(safe_name, image_file, save=True)
        return upload

    def _safe_filename(self, filename: str) -> str:
        _, ext = os.path.splitext(filename)
        ext = ext.lower().lstrip(".")
        if ext not in ALLOWED_EXTENSIONS:
            ext = "png"
        return f"{uuid.uuid4().hex}.{ext}"

    def _process_upload(self, uploaded: UploadedQuestion, image_file):
        try:
            preprocessor = ImagePreprocessor()
            preprocessed = preprocessor.preprocess(uploaded.image.path)

            ocr_service = OCRService()
            ocr_result = ocr_service.extract_text(preprocessed.path)

            uploaded.ocr_provider = ocr_result.provider
            uploaded.ocr_confidence = ocr_result.confidence

            if ocr_result.status != "success" or not ocr_result.text.strip():
                uploaded.status = "failed"
                uploaded.error_message = "OCR could not extract text from the image."
                uploaded.save()
                return

            cleaned_text = ocr_result.text.strip()
            uploaded.extracted_text = cleaned_text

            extractor = QuestionExtractor()
            candidates = extractor.extract(cleaned_text)
            uploaded.question_candidates = [
                {"index": c.index, "text": c.text} for c in candidates
            ]

            uploaded.status = "ocr_completed"
            uploaded.save()
        except Exception as exc:
            logger.exception("Processing failed for upload %s", uploaded.id)
            uploaded.status = "failed"
            uploaded.error_message = str(exc)
            uploaded.save()

    def _build_response(self, uploaded: UploadedQuestion) -> dict:
        return {
            "upload_id": uploaded.id,
            "status": uploaded.status,
            "text": uploaded.extracted_text,
            "questions": uploaded.question_candidates or [],
            "ocr_provider": uploaded.ocr_provider,
            "ocr_confidence": uploaded.ocr_confidence,
        }


class UploadStatusView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            upload = UploadedQuestion.objects.get(pk=pk, user=request.user)
        except UploadedQuestion.DoesNotExist:
            return response.Response({"success": False, "error": {"code": "NOT_FOUND", "message": "Upload not found."}}, status=status.HTTP_404_NOT_FOUND)
        serializer = UploadedQuestionSerializer(upload)
        return response.Response({"success": True, "data": serializer.data})


class UploadResultView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            upload = UploadedQuestion.objects.get(pk=pk, user=request.user)
        except UploadedQuestion.DoesNotExist:
            return response.Response({"success": False, "error": {"code": "NOT_FOUND", "message": "Upload not found."}}, status=status.HTTP_404_NOT_FOUND)
        data = {
            "upload_id": upload.id,
            "status": upload.status,
            "text": upload.extracted_text,
            "questions": upload.question_candidates or [],
            "ocr_provider": upload.ocr_provider,
            "ocr_confidence": upload.ocr_confidence,
        }
        return response.Response({"success": True, "data": data})


class UploadConfirmView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            upload = UploadedQuestion.objects.get(pk=pk, user=request.user)
        except UploadedQuestion.DoesNotExist:
            return response.Response({"success": False, "error": {"code": "NOT_FOUND", "message": "Upload not found."}}, status=status.HTTP_404_NOT_FOUND)
        upload.status = "processing"
        upload.save()
        return response.Response({"success": True, "data": {"upload_id": upload.id, "status": upload.status}})


class OCRExtractView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return response.Response({"detail": "Not implemented in Phase 7."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class UploadSolveSelectedView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UploadSolveSerializer

    def post(self, request):
        serializer = UploadSolveSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response({"success": False, "error": {"code": "VALIDATION_ERROR", "message": serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)

        upload_id = serializer.validated_data["upload_id"]
        question_index = serializer.validated_data["question_index"]

        try:
            upload = UploadedQuestion.objects.get(pk=upload_id, user=request.user)
        except UploadedQuestion.DoesNotExist:
            return response.Response({"success": False, "error": {"code": "NOT_FOUND", "message": "Upload not found."}}, status=status.HTTP_404_NOT_FOUND)

        if upload.status != "ocr_completed":
            return response.Response({"success": False, "error": {"code": "OCR_NOT_READY", "message": "OCR processing has not completed for this upload."}}, status=status.HTTP_400_BAD_REQUEST)

        if not upload.extracted_text or not upload.extracted_text.strip():
            return response.Response({"success": False, "error": {"code": "OCR_TEXT_EMPTY", "message": "OCR did not extract any text from this image."}}, status=status.HTTP_400_BAD_REQUEST)

        candidates = upload.question_candidates or []
        if not candidates:
            return response.Response({"success": False, "error": {"code": "NO_QUESTIONS", "message": "No question candidates were extracted from this image."}}, status=status.HTTP_400_BAD_REQUEST)

        if question_index < 1 or question_index > len(candidates):
            return response.Response({"success": False, "error": {"code": "INVALID_QUESTION_INDEX", "message": f"question_index must be between 1 and {len(candidates)}."}}, status=status.HTTP_400_BAD_REQUEST)

        selected = candidates[question_index - 1]
        selected_text = selected.get("text", "").strip()
        if not selected_text:
            return response.Response({"success": False, "error": {"code": "EMPTY_QUESTION", "message": "Selected question text is empty."}}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service = SolveService()
            result = service.solve(request.user, selected_text, uploaded_question=upload)
            return response.Response({"success": True, "data": result}, status=status.HTTP_200_OK)
        except ValueError as exc:
            return response.Response({"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            logger.warning("OCR solve AI runtime error: %s", exc)
            return response.Response({"success": False, "error": {"code": "AI_UNAVAILABLE", "message": "AI solver is temporarily unavailable."}}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as exc:
            logger.exception("Unexpected OCR solve error")
            return response.Response({"success": False, "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
