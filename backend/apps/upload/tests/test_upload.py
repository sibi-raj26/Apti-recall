import io
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image as PILImage
from rest_framework.test import APIClient

from backend.apps.users.models import User
from backend.apps.questions.models import UploadedQuestion
from backend.ai_services.ocr.base import OCRResult
from backend.apps.upload.services.image_preprocessor import PreprocessedImage
from backend.apps.upload.services.question_extractor import QuestionExtractor


def _create_test_image(format_name="PNG", size=(100, 50), color=(255, 255, 255)):
    image = PILImage.new("RGB", size, color)
    buffer = io.BytesIO()
    image.save(buffer, format=format_name)
    buffer.seek(0)
    return buffer


def _create_uploaded_image(format_name="PNG", size=(100, 50), color=(255, 255, 255)):
    image = PILImage.new("RGB", size, color)
    _, ext = os.path.splitext(f"test.{format_name.lower()}")
    buffer = io.BytesIO()
    image.save(buffer, format=format_name)
    buffer.seek(0)
    buffer.name = f"test{ext}"
    return buffer, ext


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="uploaduser@example.com", username="uploaduser", password="testpass123")


@pytest.fixture
def auth_client(api_client, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def upload_url():
    return "/api/upload/image/"


class TestAnonymousUploadRejected:
    def test_anonymous_upload_rejected(self, api_client, upload_url):
        buffer, ext = _create_uploaded_image()
        response = api_client.post(
            upload_url,
            data={"image": buffer},
            format="multipart",
        )
        assert response.status_code == 401


class TestValidImageAccepted:
    @patch("backend.apps.upload.views.OCRService")
    @patch("backend.apps.upload.views.ImagePreprocessor")
    def test_valid_image_accepted(self, mock_preprocessor_cls, mock_ocr_cls, auth_client, upload_url, db):
        mock_preprocessed = PreprocessedImage(
            path="/tmp/test_processed.png",
            width=100,
            height=50,
            format="PNG",
        )
        mock_preprocessor = MagicMock()
        mock_preprocessor.preprocess.return_value = mock_preprocessed
        mock_preprocessor_cls.return_value = mock_preprocessor

        mock_ocr_result = OCRResult(
            text="What is 20% of 150?",
            confidence=0.95,
            provider="tesseract",
            language="eng",
            status="success",
        )
        mock_ocr_service = MagicMock()
        mock_ocr_service.extract_text.return_value = mock_ocr_result
        mock_ocr_cls.return_value = mock_ocr_service

        buffer, ext = _create_uploaded_image("PNG")
        response = auth_client.post(
            upload_url,
            data={"image": buffer},
            format="multipart",
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["data"]["status"] == "ocr_completed"
        assert "What is 20% of 150?" in response.json()["data"]["text"]


class TestUnsupportedFileRejected:
    def test_unsupported_file_rejected(self, auth_client, upload_url):
        buffer = io.BytesIO(b"This is a plain text file, not an image.")
        buffer.name = "malicious.txt"
        response = auth_client.post(
            upload_url,
            data={"image": buffer},
            format="multipart",
        )
        assert response.status_code == 400


class TestOversizedFileRejected:
    def test_oversized_file_rejected(self, auth_client, upload_url, settings):
        settings.MAX_UPLOAD_SIZE = 100
        buffer, ext = _create_uploaded_image("PNG")
        buffer.seek(0)
        buffer.write(b"\x00" * 200)
        buffer.seek(0)
        buffer.name = f"large{ext}"
        response = auth_client.post(
            upload_url,
            data={"image": buffer},
            format="multipart",
        )
        assert response.status_code == 400


class TestFilenamePathSafety:
    @patch("backend.apps.upload.views.OCRService")
    @patch("backend.apps.upload.views.ImagePreprocessor")
    def test_path_traversal_filename_rejected(self, mock_preprocessor_cls, mock_ocr_cls, auth_client, upload_url, db):
        mock_preprocessed = PreprocessedImage(
            path="/tmp/test_processed.png",
            width=100,
            height=50,
            format="PNG",
        )
        mock_preprocessor = MagicMock()
        mock_preprocessor.preprocess.return_value = mock_preprocessed
        mock_preprocessor_cls.return_value = mock_preprocessor

        mock_ocr_result = OCRResult(
            text="Some question text.",
            confidence=0.9,
            provider="tesseract",
            language="eng",
            status="success",
        )
        mock_ocr_service = MagicMock()
        mock_ocr_service.extract_text.return_value = mock_ocr_result
        mock_ocr_cls.return_value = mock_ocr_service

        buffer, ext = _create_uploaded_image("PNG")
        buffer.name = "../../evil.png"
        response = auth_client.post(
            upload_url,
            data={"image": buffer},
            format="multipart",
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

        upload_id = response.json()["data"]["upload_id"]
        upload = UploadedQuestion.objects.get(pk=upload_id)
        assert ".." not in upload.image.name
        assert upload.image.name.startswith("uploads/questions/")


class TestOCRProviderMockable:
    def test_ocr_provider_can_be_mocked(self):
        from backend.ai_services.ocr.service import OCRService
        from backend.ai_services.ocr.tesseract import TesseractOCRProvider

        mock_provider = MagicMock(spec=TesseractOCRProvider)
        mock_provider.extract_text.return_value = OCRResult(
            text="Mocked text",
            confidence=1.0,
            provider="mock",
            language="eng",
            status="success",
        )

        service = OCRService(provider=mock_provider)
        result = service.extract_text("/tmp/fake.png")
        assert result.text == "Mocked text"
        assert result.provider == "mock"
        mock_provider.extract_text.assert_called_once_with("/tmp/fake.png", language="eng")


class TestOCRSuccessStoresText:
    @patch("backend.apps.upload.views.OCRService")
    @patch("backend.apps.upload.views.ImagePreprocessor")
    def test_ocr_success_stores_extracted_text(
        self, mock_preprocessor_cls, mock_ocr_cls, auth_client, upload_url, db
    ):
        mock_preprocessed = PreprocessedImage(
            path="/tmp/test_processed.png",
            width=100,
            height=50,
            format="PNG",
        )
        mock_preprocessor = MagicMock()
        mock_preprocessor.preprocess.return_value = mock_preprocessed
        mock_preprocessor_cls.return_value = mock_preprocessor

        mock_ocr_result = OCRResult(
            text="A train travels 120 km in 2 hours.",
            confidence=0.87,
            provider="tesseract",
            language="eng",
            status="success",
        )
        mock_ocr_service = MagicMock()
        mock_ocr_service.extract_text.return_value = mock_ocr_result
        mock_ocr_cls.return_value = mock_ocr_service

        buffer, ext = _create_uploaded_image("PNG")
        response = auth_client.post(
            upload_url,
            data={"image": buffer},
            format="multipart",
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "ocr_completed"
        assert response.json()["data"]["ocr_provider"] == "tesseract"
        assert response.json()["data"]["ocr_confidence"] == 0.87
        assert response.json()["data"]["text"] == "A train travels 120 km in 2 hours."

        upload_id = response.json()["data"]["upload_id"]
        upload = UploadedQuestion.objects.get(pk=upload_id)
        assert upload.status == "ocr_completed"
        assert upload.extracted_text == "A train travels 120 km in 2 hours."
        assert upload.ocr_provider == "tesseract"
        assert upload.ocr_confidence == 0.87


class TestOCRFailureControlled:
    @patch("backend.apps.upload.views.OCRService")
    @patch("backend.apps.upload.views.ImagePreprocessor")
    def test_ocr_failure_returns_controlled_failure(
        self, mock_preprocessor_cls, mock_ocr_cls, auth_client, upload_url, db
    ):
        mock_preprocessed = PreprocessedImage(
            path="/tmp/test_processed.png",
            width=100,
            height=50,
            format="PNG",
        )
        mock_preprocessor = MagicMock()
        mock_preprocessor.preprocess.return_value = mock_preprocessed
        mock_preprocessor_cls.return_value = mock_preprocessor

        mock_ocr_result = OCRResult(
            text="",
            confidence=None,
            provider="tesseract",
            language="eng",
            status="failed",
        )
        mock_ocr_service = MagicMock()
        mock_ocr_service.extract_text.return_value = mock_ocr_result
        mock_ocr_cls.return_value = mock_ocr_service

        buffer, ext = _create_uploaded_image("PNG")
        response = auth_client.post(
            upload_url,
            data={"image": buffer},
            format="multipart",
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "failed"
        assert response.json()["data"]["text"] == ""

        upload_id = response.json()["data"]["upload_id"]
        upload = UploadedQuestion.objects.get(pk=upload_id)
        assert upload.status == "failed"
        assert upload.extracted_text == ""


class TestTextNormalization:
    def test_text_normalization(self):
        extractor = QuestionExtractor()
        raw = "1.  What   is   \n\n\n   20%   of   150?\n\n\n\n2.  Find    the    average."
        cleaned = extractor._normalize(raw)
        assert "   " not in cleaned
        assert cleaned.startswith("1. What is")
        assert "\n\n\n" not in cleaned


class TestMultipleQuestionsExtracted:
    def test_multiple_questions_extracted(self):
        extractor = QuestionExtractor()
        text = (
            "1. A train travels 120 km in 2 hours.\n"
            "2. Find the average speed.\n"
            "3. Calculate the distance.\n"
        )
        candidates = extractor.extract(text)
        assert len(candidates) == 3
        assert candidates[0].index == 1
        assert "120 km" in candidates[0].text
        assert candidates[1].index == 2
        assert "average speed" in candidates[1].text
        assert candidates[2].index == 3
        assert "distance" in candidates[2].text


class TestSingleQuestionRemainsOneCandidate:
    def test_single_question_remains_one_candidate(self):
        extractor = QuestionExtractor()
        text = "What is 20% of 150?"
        candidates = extractor.extract(text)
        assert len(candidates) == 1
        assert candidates[0].index == 1
        assert candidates[0].text == "What is 20% of 150?"


class TestEmptyPoorOCRResult:
    @patch("backend.apps.upload.views.OCRService")
    @patch("backend.apps.upload.views.ImagePreprocessor")
    def test_empty_ocr_result_returns_failed_status(
        self, mock_preprocessor_cls, mock_ocr_cls, auth_client, upload_url, db
    ):
        mock_preprocessed = PreprocessedImage(
            path="/tmp/test_processed.png",
            width=100,
            height=50,
            format="PNG",
        )
        mock_preprocessor = MagicMock()
        mock_preprocessor.preprocess.return_value = mock_preprocessed
        mock_preprocessor_cls.return_value = mock_preprocessor

        mock_ocr_result = OCRResult(
            text="   \n  \n   ",
            confidence=None,
            provider="tesseract",
            language="eng",
            status="success",
        )
        mock_ocr_service = MagicMock()
        mock_ocr_service.extract_text.return_value = mock_ocr_result
        mock_ocr_cls.return_value = mock_ocr_service

        buffer, ext = _create_uploaded_image("PNG")
        response = auth_client.post(
            upload_url,
            data={"image": buffer},
            format="multipart",
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "failed"

        upload_id = response.json()["data"]["upload_id"]
        upload = UploadedQuestion.objects.get(pk=upload_id)
        assert upload.status == "failed"
