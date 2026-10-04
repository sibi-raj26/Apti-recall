import io
import os
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image as PILImage
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from backend.apps.users.models import User
from backend.apps.questions.models import UploadedQuestion
from backend.ai_services.ocr.base import OCRResult
from backend.apps.upload.services.image_preprocessor import PreprocessedImage
from backend.apps.upload.services.question_extractor import QuestionExtractor
from backend.apps.upload.serializers import UploadSolveSerializer


def _create_test_image(format_name="PNG", size=(100, 50), color=(255, 255, 255)):
    image = PILImage.new("RGB", size, color)
    buffer = io.BytesIO()
    image.save(buffer, format=format_name)
    buffer.seek(0)
    buffer.name = f"test.{format_name.lower()}"
    return buffer


def _create_uploaded_question_with_ocr(user, extracted_text="A train travels 120 km in 2 hours. Find its average speed.", question_candidates=None):
    if question_candidates is None:
        question_candidates = [{"index": 1, "text": extracted_text}]
    return UploadedQuestion.objects.create(
        user=user,
        image="uploads/questions/test.png",
        extracted_text=extracted_text,
        status="ocr_completed",
        question_candidates=question_candidates,
        ocr_provider="tesseract",
        ocr_confidence=0.9,
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="phase8user@example.com", username="phase8user", password="testpass123")


@pytest.fixture
def auth_client(api_client, user):
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def other_user(db):
    return User.objects.create_user(email="otheruser@example.com", username="otheruser", password="testpass123")


@pytest.fixture
def other_auth_client(api_client, other_user):
    refresh = RefreshToken.for_user(other_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def upload_with_ocr(user):
    return _create_uploaded_question_with_ocr(user)


@pytest.fixture
def upload_url():
    return "/api/upload/solve/"


class TestUnauthenticatedRejected:
    def test_unauthenticated_solve_rejected(self, api_client, upload_url):
        response = api_client.post(upload_url, {"upload_id": 1, "question_index": 1}, format="json")
        assert response.status_code == 401


class TestValidSelectedQuestion:
    @patch("backend.apps.upload.views.SolveService")
    def test_valid_selected_question_calls_solver(self, mock_solver_cls, auth_client, upload_url, user, upload_with_ocr):
        mock_result = {
            "question_text": "A train travels 120 km in 2 hours. Find its average speed.",
            "topic": {"id": 1, "name": "Time Speed Distance"},
            "problem_type": {"id": 1, "name": "average-speed"},
            "concept": "Average speed = total distance / total time.",
            "approach": "Divide distance by time.",
            "steps": [{"step": 1, "title": "Calculate", "calculation": "120 / 2", "explanation": "Divide distance by time."}],
            "final_answer": "60 km/h",
            "shortcut": "",
            "confidence": 0.9,
            "verification_status": "VERIFIED",
            "verification_details": {},
            "source": "ai_generated",
            "attempt_id": 1,
        }
        mock_solver = MagicMock()
        mock_solver.solve.return_value = mock_result
        mock_solver_cls.return_value = mock_solver

        response = auth_client.post(upload_url, {"upload_id": upload_with_ocr.id, "question_index": 1}, format="json")
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_solver.solve.assert_called_once()
        called_args = mock_solver.solve.call_args
        assert called_args[0][0] == user
        assert "120 km" in called_args[0][1]
        assert called_args[1]["uploaded_question"] == upload_with_ocr


class TestMultipleQuestionsSelectOnlyOne:
    @patch("backend.apps.upload.views.SolveService")
    def test_selecting_question_2_sends_only_question_2(self, mock_solver_cls, auth_client, upload_url, user):
        upload = _create_uploaded_question_with_ocr(
            user,
            extracted_text="1. What is 20% of 150?\n2. A train travels 120 km in 2 hours. Find its average speed.",
            question_candidates=[
                {"index": 1, "text": "What is 20% of 150?"},
                {"index": 2, "text": "A train travels 120 km in 2 hours. Find its average speed."},
            ],
        )

        mock_solver = MagicMock()
        mock_solver.solve.return_value = {
            "question_text": "A train travels 120 km in 2 hours. Find its average speed.",
            "topic": None,
            "problem_type": None,
            "concept": "",
            "approach": "",
            "steps": [],
            "final_answer": "60 km/h",
            "shortcut": "",
            "confidence": 0.0,
            "verification_status": "UNABLE_TO_VERIFY",
            "verification_details": {},
            "source": "ai_generated",
            "attempt_id": 1,
        }
        mock_solver_cls.return_value = mock_solver

        response = auth_client.post(upload_url, {"upload_id": upload.id, "question_index": 2}, format="json")
        assert response.status_code == 200
        called_text = mock_solver.solve.call_args[0][1]
        assert "20%" not in called_text
        assert "120 km" in called_text


class TestInvalidIndex:
    @patch("backend.apps.upload.views.SolveService")
    def test_invalid_index_returns_400(self, mock_solver_cls, auth_client, upload_url, upload_with_ocr):
        response = auth_client.post(upload_url, {"upload_id": upload_with_ocr.id, "question_index": 3}, format="json")
        assert response.status_code == 400
        mock_solver_cls.return_value.solve.assert_not_called()


class TestEmptyOCRText:
    def test_empty_ocr_returns_400(self, auth_client, upload_url, user):
        upload = UploadedQuestion.objects.create(
            user=user,
            image="uploads/questions/empty.png",
            extracted_text="",
            status="ocr_completed",
            question_candidates=[],
        )
        response = auth_client.post(upload_url, {"upload_id": upload.id, "question_index": 1}, format="json")
        assert response.status_code == 400


class TestOwnership:
    @patch("backend.apps.upload.views.SolveService")
    def test_other_user_cannot_solve(self, mock_solver_cls, other_auth_client, upload_url, upload_with_ocr):
        response = other_auth_client.post(upload_url, {"upload_id": upload_with_ocr.id, "question_index": 1}, format="json")
        assert response.status_code == 404
        mock_solver_cls.return_value.solve.assert_not_called()


class TestExistingSolverIntegration:
    @patch("backend.apps.upload.views.SolveService")
    def test_existing_solver_is_used(self, mock_solver_cls, auth_client, upload_url, user, upload_with_ocr):
        mock_solver = MagicMock()
        mock_solver.solve.return_value = {
            "question_text": "text",
            "topic": None,
            "problem_type": None,
            "concept": "",
            "approach": "",
            "steps": [],
            "final_answer": "42",
            "shortcut": "",
            "confidence": 0.0,
            "verification_status": "UNABLE_TO_VERIFY",
            "verification_details": {},
            "source": "ai_generated",
            "attempt_id": 1,
        }
        mock_solver_cls.return_value = mock_solver

        response = auth_client.post(upload_url, {"upload_id": upload_with_ocr.id, "question_index": 1}, format="json")
        assert response.status_code == 200
        mock_solver_cls.assert_called_once()
        assert mock_solver.solve.call_args[0][0] == user


class TestVerificationIntegration:
    @patch("backend.apps.upload.views.SolveService")
    def test_verification_result_in_response(self, mock_solver_cls, auth_client, upload_url, user, upload_with_ocr):
        mock_solver = MagicMock()
        mock_solver.solve.return_value = {
            "question_text": "A train travels 120 km in 2 hours. Find its average speed.",
            "topic": {"id": 1, "name": "Time Speed Distance"},
            "problem_type": {"id": 1, "name": "average-speed"},
            "concept": "Average speed = distance / time.",
            "approach": "Divide total distance by total time.",
            "steps": [{"step": 1, "title": "Calculate", "calculation": "120 / 2", "explanation": "Divide distance by time."}],
            "final_answer": "60 km/h",
            "shortcut": "",
            "confidence": 0.9,
            "verification_status": "VERIFIED",
            "verification_details": {"method": "TIME_SPEED_DISTANCE", "checks": []},
            "source": "ai_generated",
            "attempt_id": 1,
        }
        mock_solver_cls.return_value = mock_solver

        response = auth_client.post(upload_url, {"upload_id": upload_with_ocr.id, "question_index": 1}, format="json")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["verification_status"] == "VERIFIED"
        assert "attempt_id" in data


class TestSolverUnavailable:
    @patch("backend.apps.upload.views.SolveService")
    def test_solver_unavailable_returns_503(self, mock_solver_cls, auth_client, upload_url, upload_with_ocr):
        mock_solver = MagicMock()
        mock_solver.solve.side_effect = RuntimeError("Provider down")
        mock_solver_cls.return_value = mock_solver

        response = auth_client.post(upload_url, {"upload_id": upload_with_ocr.id, "question_index": 1}, format="json")
        assert response.status_code == 503


class TestSolverTimeout:
    @patch("backend.apps.upload.views.SolveService")
    def test_solver_timeout_returns_controlled_error(self, mock_solver_cls, auth_client, upload_url, upload_with_ocr):
        import requests
        mock_solver = MagicMock()
        mock_solver.solve.side_effect = requests.exceptions.Timeout("Timed out")
        mock_solver_cls.return_value = mock_solver

        response = auth_client.post(upload_url, {"upload_id": upload_with_ocr.id, "question_index": 1}, format="json")
        assert response.status_code == 500


class TestSourceMetadata:
    @patch("backend.apps.upload.views.SolveService")
    def test_user_attempt_links_uploaded_question(self, mock_solver_cls, auth_client, upload_url, user, upload_with_ocr):
        mock_solver = MagicMock()
        mock_solver.solve.return_value = {
            "question_text": "A train travels 120 km in 2 hours. Find its average speed.",
            "topic": None,
            "problem_type": None,
            "concept": "",
            "approach": "",
            "steps": [],
            "final_answer": "60 km/h",
            "shortcut": "",
            "confidence": 0.0,
            "verification_status": "UNABLE_TO_VERIFY",
            "verification_details": {},
            "source": "ai_generated",
            "attempt_id": 1,
        }
        mock_solver_cls.return_value = mock_solver

        response = auth_client.post(upload_url, {"upload_id": upload_with_ocr.id, "question_index": 1}, format="json")
        assert response.status_code == 200
        called_kwargs = mock_solver.solve.call_args[1]
        assert called_kwargs["uploaded_question"] == upload_with_ocr


class TestExistingTextSolverRegression:
    def test_existing_text_solver_still_works(self, auth_client):
        from backend.apps.upload.serializers import UploadQuestionSerializer

        buffer = _create_test_image("PNG")
        response = auth_client.post("/api/upload/image/", data={"image": buffer}, format="multipart")
        assert response.status_code == 200
