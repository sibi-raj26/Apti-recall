import io
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image as PILImage

from backend.ai_services.ocr.base import OCRResult
from backend.ai_services.ocr.service import OCRService
from backend.ai_services.ocr.tesseract import TesseractOCRProvider
from backend.apps.upload.services.image_preprocessor import ImagePreprocessor
from backend.apps.upload.services.question_extractor import QuestionExtractor


def _create_test_image(format_name="PNG", size=(100, 50), color=(255, 255, 255)):
    image = PILImage.new("RGB", size, color)
    buffer = io.BytesIO()
    image.save(buffer, format=format_name)
    buffer.seek(0)
    return buffer


class TestOCRServiceContract:
    def test_returns_ocr_result_object(self):
        service = OCRService()
        result = service.extract_text("/nonexistent/image.png")
        assert isinstance(result, OCRResult)
        assert result.provider in {"tesseract", "unknown"}
        assert result.status in {"success", "failed"}

    def test_missing_image_returns_failed_status(self):
        service = OCRService()
        result = service.extract_text("/nonexistent/image.png")
        assert result.status == "failed"
        assert result.text == ""

    def test_tesseract_provider_returns_text_success_path(self):
        import sys
        mock_pytesseract = MagicMock()
        sys.modules["pytesseract"] = mock_pytesseract
        mock_pytesseract.image_to_string.return_value = "What is 20% of 150?"

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image = PILImage.new("RGB", (100, 50), (255, 255, 255))
            image.save(tmp.name)
            provider = TesseractOCRProvider()
            result = provider.extract_text(tmp.name)
            assert result.status == "success"
            assert "20%" in result.text
            tmp_path = tmp.name
        try:
            os.unlink(tmp_path)
        except PermissionError:
            pass
        del sys.modules["pytesseract"]

    def test_preprocessor_returns_processed_image(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image = PILImage.new("RGB", (200, 100), (255, 255, 255))
            image.save(tmp.name)
            preprocessor = ImagePreprocessor()
            processed = preprocessor.preprocess(tmp.name)
            assert os.path.exists(processed.path)
        os.unlink(tmp.name)
        if os.path.exists(processed.path):
            os.unlink(processed.path)

    def test_question_extractor_returns_candidates(self):
        extractor = QuestionExtractor()
        raw_text = "1. What is 20% of 150?\n2. A train travels 120 km in 2 hours."
        candidates = extractor.extract(raw_text)
        assert len(candidates) == 2
        assert "What is 20% of 150?" in candidates[0].text

    def test_ocr_upload_endpoint_returns_expected_fields(self, db):
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        from backend.apps.users.models import User
        from backend.apps.upload.services.image_preprocessor import PreprocessedImage
        from unittest.mock import MagicMock, patch

        user = User.objects.create_user(email="ocr@example.com", username="ocruser", password="ocrpass123")
        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        buffer = _create_test_image("PNG")
        buffer.name = "test.png"

        mock_preprocessed = PreprocessedImage(path="/tmp/test.png", width=100, height=50, format="PNG")
        mock_ocr = OCRResult(text="What is 20% of 150?", confidence=0.9, provider="tesseract", language="eng", status="success")

        with patch("backend.apps.upload.views.ImagePreprocessor") as mock_preprocessor_cls, \
             patch("backend.apps.upload.views.OCRService") as mock_ocr_cls:
            mock_preprocessor_cls.return_value = MagicMock(preprocess=MagicMock(return_value=mock_preprocessed))
            mock_ocr_cls.return_value = MagicMock(extract_text=MagicMock(return_value=mock_ocr))

            response = client.post("/api/upload/image/", {"image": buffer}, format="multipart")
            assert response.status_code == 200
            data = response.data["data"]
            assert "upload_id" in data
            assert "status" in data
            assert "questions" in data
            assert data["ocr_provider"] == "tesseract"
