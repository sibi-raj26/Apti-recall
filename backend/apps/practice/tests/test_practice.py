import logging
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from backend.apps.users.models import User
from backend.apps.topics.models import Topic, ProblemType
from backend.apps.questions.models import Question, UploadedQuestion
from backend.apps.practice.services.practice_service import PracticeService


logger = logging.getLogger(__name__)


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="practice@example.com", username="practiceuser", password="practicepass123")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def other_user(db):
    return User.objects.create_user(email="otherpractice@example.com", username="otherpractice", password="practicepass123")


@pytest.fixture
def topic(db):
    return Topic.objects.create(name="Time Speed Distance", slug="time-speed-distance", order=1)


@pytest.fixture
def problem_type(db, topic):
    return ProblemType.objects.create(topic=topic, name="average-speed", description="Average speed problems")


@pytest.fixture
def source_question(db, topic, problem_type, user):
    return Question.objects.create(
        topic=topic,
        problem_type=problem_type,
        difficulty="easy",
        question_text="A train travels 120 km in 2 hours. Find its average speed.",
        correct_answer="60 km/h",
        explanation_concept="Average speed = total distance / total time.",
        explanation_approach="Divide distance by time.",
        explanation_steps=[],
        is_active=True,
        created_by=user,
    )


@pytest.fixture
def upload_with_ocr(user, topic, problem_type):
    return UploadedQuestion.objects.create(
        user=user,
        image="uploads/questions/practice.png",
        extracted_text="A train travels 120 km in 2 hours. Find its average speed.",
        detected_topic=topic,
        detected_problem_type=problem_type,
        status="ocr_completed",
        question_candidates=[{"index": 1, "text": "A train travels 120 km in 2 hours. Find its average speed."}],
        ocr_provider="tesseract",
        ocr_confidence=0.9,
    )


class TestUnauthenticatedRejected:
    def test_unauthenticated_practice_rejected(self, api_client):
        response = api_client.post("/api/practice/generate/", {"question_id": 1}, format="json")
        assert response.status_code == 401


class TestValidGenerationFromQuestion:
    @patch("backend.apps.practice.views.PracticeService")
    def test_valid_generation_from_question_id(self, mock_practice_cls, auth_client, source_question):
        mock_practice = MagicMock()
        mock_practice.generate_similar_question.return_value = {
            "question_text": "A train travels 180 km in 3 hours. Find its average speed.",
            "topic": {"id": 1, "name": "Time Speed Distance"},
            "problem_type": {"id": 1, "name": "average-speed"},
            "difficulty": "easy",
            "concept": "Average speed = total distance / total time.",
            "approach": "Divide distance by time.",
            "steps": [{"step": 1, "title": "Calculate", "calculation": "180 / 3 = 60", "explanation": "Divide distance by time."}],
            "final_answer": "60 km/h",
            "shortcut": "",
            "confidence": 0.9,
            "verification_status": "VERIFIED",
            "verification_details": {"method": "TIME_SPEED_DISTANCE", "checks": []},
            "source": "practice_generated",
            "attempt": 1,
        }
        mock_practice_cls.return_value = mock_practice

        response = auth_client.post("/api/practice/generate/", {"question_id": source_question.id}, format="json")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["data"]["verification_status"] == "VERIFIED"
        mock_practice.generate_similar_question.assert_called_once()


class TestSimilarityRequirements:
    @patch("backend.apps.practice.views.PracticeService")
    def test_generation_preserves_topic_and_difficulty(self, mock_practice_cls, auth_client, source_question):
        mock_practice = MagicMock()
        mock_practice.generate_similar_question.return_value = {
            "question_text": "A train travels 180 km in 3 hours. Find its average speed.",
            "topic": {"id": 1, "name": "Time Speed Distance"},
            "problem_type": {"id": 1, "name": "average-speed"},
            "difficulty": "easy",
            "concept": "Average speed",
            "approach": "Divide distance by time.",
            "steps": [],
            "final_answer": "60 km/h",
            "shortcut": "",
            "confidence": 0.9,
            "verification_status": "VERIFIED",
            "verification_details": {},
            "source": "practice_generated",
            "attempt": 1,
        }
        mock_practice_cls.return_value = mock_practice

        response = auth_client.post("/api/practice/generate/", {"question_id": source_question.id}, format="json")
        assert response.status_code == 200
        called_kwargs = mock_practice.generate_similar_question.call_args[1]
        assert called_kwargs["difficulty"] == "easy"
        assert called_kwargs["topic"] == "Time Speed Distance"
        assert called_kwargs["problem_type"] == "average-speed"


class TestDuplicatePrevention:
    @patch("backend.apps.practice.views.PracticeService")
    def test_duplicate_question_triggers_regeneration(self, mock_practice_cls, auth_client, source_question):
        mock_practice = MagicMock()
        mock_practice.generate_similar_question.return_value = {
            "question_text": "A train travels 180 km in 3 hours. Find its average speed.",
            "topic": {"id": 1, "name": "Time Speed Distance"},
            "problem_type": {"id": 1, "name": "average-speed"},
            "difficulty": "easy",
            "concept": "Average speed",
            "approach": "Divide distance by time.",
            "steps": [],
            "final_answer": "60 km/h",
            "shortcut": "",
            "confidence": 0.9,
            "verification_status": "VERIFIED",
            "verification_details": {},
            "source": "practice_generated",
            "attempt": 1,
            "duplicate_found": False,
        }
        mock_practice_cls.return_value = mock_practice

        response = auth_client.post("/api/practice/generate/", {"question_id": source_question.id}, format="json")
        assert response.status_code == 200
        assert mock_practice.generate_similar_question.called


class TestMathematicalVerificationRequired:
    @patch("backend.apps.practice.views.PracticeService")
    def test_verified_question_returned(self, mock_practice_cls, auth_client, source_question):
        mock_practice = MagicMock()
        mock_practice.generate_similar_question.return_value = {
            "question_text": "A train travels 180 km in 3 hours. Find its average speed.",
            "topic": {"id": 1, "name": "Time Speed Distance"},
            "problem_type": {"id": 1, "name": "average-speed"},
            "difficulty": "easy",
            "concept": "Average speed",
            "approach": "Divide distance by time.",
            "steps": [{"step": 1, "title": "Calculate", "calculation": "180 / 3 = 60", "explanation": "Divide."}],
            "final_answer": "60 km/h",
            "shortcut": "",
            "confidence": 0.9,
            "verification_status": "VERIFIED",
            "verification_details": {"method": "TIME_SPEED_DISTANCE", "checks": []},
            "source": "practice_generated",
            "attempt": 1,
        }
        mock_practice_cls.return_value = mock_practice

        response = auth_client.post("/api/practice/generate/", {"question_id": source_question.id}, format="json")
        assert response.status_code == 200
        assert response.json()["data"]["verification_status"] == "VERIFIED"


class TestAcceptanceRule:
    @patch("backend.apps.practice.views.PracticeService")
    def test_failed_verification_not_marked_verified(self, mock_practice_cls, auth_client, source_question):
        mock_practice = MagicMock()
        mock_practice.generate_similar_question.return_value = {
            "question_text": "A train travels 180 km in 3 hours. Find its average speed.",
            "topic": {"id": 1, "name": "Time Speed Distance"},
            "problem_type": {"id": 1, "name": "average-speed"},
            "difficulty": "easy",
            "concept": "Average speed",
            "approach": "Divide distance by time.",
            "steps": [],
            "final_answer": "90 km/h",
            "shortcut": "",
            "confidence": 0.9,
            "verification_status": "FAILED",
            "verification_details": {"method": "TIME_SPEED_DISTANCE", "details": "Math mismatch."},
            "source": "practice_generated",
            "attempt": 3,
        }
        mock_practice_cls.return_value = mock_practice

        response = auth_client.post("/api/practice/generate/", {"question_id": source_question.id}, format="json")
        assert response.status_code == 200
        assert response.json()["data"]["verification_status"] == "FAILED"


class TestRetryOnFailure:
    @patch("backend.apps.practice.views.PracticeService")
    def test_service_retries_on_failed_verification(self, mock_practice_cls, auth_client, source_question):
        mock_practice = MagicMock()
        mock_practice.generate_similar_question.return_value = {
            "question_text": "A train travels 180 km in 3 hours. Find its average speed.",
            "topic": {"id": 1, "name": "Time Speed Distance"},
            "problem_type": {"id": 1, "name": "average-speed"},
            "difficulty": "easy",
            "concept": "Average speed",
            "approach": "Divide distance by time.",
            "steps": [],
            "final_answer": "60 km/h",
            "shortcut": "",
            "confidence": 0.9,
            "verification_status": "VERIFIED",
            "verification_details": {},
            "source": "practice_generated",
            "attempt": 2,
        }
        mock_practice_cls.return_value = mock_practice

        response = auth_client.post("/api/practice/generate/", {"question_id": source_question.id}, format="json")
        assert response.status_code == 200
        assert mock_practice.generate_similar_question.called


class TestSourceMetadata:
    @patch("backend.apps.practice.views.PracticeService")
    def test_practice_result_includes_source_metadata(self, mock_practice_cls, auth_client, source_question):
        mock_practice = MagicMock()
        mock_practice.generate_similar_question.return_value = {
            "question_text": "A train travels 180 km in 3 hours. Find its average speed.",
            "topic": {"id": 1, "name": "Time Speed Distance"},
            "problem_type": {"id": 1, "name": "average-speed"},
            "difficulty": "easy",
            "concept": "Average speed",
            "approach": "Divide distance by time.",
            "steps": [],
            "final_answer": "60 km/h",
            "shortcut": "",
            "confidence": 0.9,
            "verification_status": "VERIFIED",
            "verification_details": {},
            "source": "practice_generated",
            "attempt": 1,
        }
        mock_practice_cls.return_value = mock_practice

        response = auth_client.post("/api/practice/generate/", {"question_id": source_question.id}, format="json")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["source"] == "practice_generated"
        assert "verification_status" in data
        assert "verification_details" in data


class TestExistingQuestionSource:
    @patch("backend.apps.practice.views.PracticeService")
    def test_existing_question_as_source(self, mock_practice_cls, auth_client, source_question):
        mock_practice = MagicMock()
        mock_practice.generate_similar_question.return_value = {
            "question_text": "A train travels 180 km in 3 hours. Find its average speed.",
            "topic": {"id": 1, "name": "Time Speed Distance"},
            "problem_type": {"id": 1, "name": "average-speed"},
            "difficulty": "easy",
            "concept": "Average speed",
            "approach": "Divide distance by time.",
            "steps": [],
            "final_answer": "60 km/h",
            "shortcut": "",
            "confidence": 0.9,
            "verification_status": "VERIFIED",
            "verification_details": {},
            "source": "practice_generated",
            "attempt": 1,
        }
        mock_practice_cls.return_value = mock_practice

        response = auth_client.post("/api/practice/generate/", {"question_id": source_question.id}, format="json")
        assert response.status_code == 200
        called_kwargs = mock_practice.generate_similar_question.call_args[1]
        assert called_kwargs["source_question"] == source_question


class TestOCRSource:
    @patch("backend.apps.practice.views.PracticeService")
    def test_ocr_upload_as_source(self, mock_practice_cls, auth_client, upload_with_ocr):
        mock_practice = MagicMock()
        mock_practice.generate_similar_question.return_value = {
            "question_text": "A train travels 180 km in 3 hours. Find its average speed.",
            "topic": {"id": 1, "name": "Time Speed Distance"},
            "problem_type": {"id": 1, "name": "average-speed"},
            "difficulty": "easy",
            "concept": "Average speed",
            "approach": "Divide distance by time.",
            "steps": [],
            "final_answer": "60 km/h",
            "shortcut": "",
            "confidence": 0.9,
            "verification_status": "VERIFIED",
            "verification_details": {},
            "source": "practice_generated",
            "attempt": 1,
        }
        mock_practice_cls.return_value = mock_practice

        response = auth_client.post("/api/practice/generate/", {"upload_id": upload_with_ocr.id, "question_index": 1}, format="json")
        assert response.status_code == 200
        called_kwargs = mock_practice.generate_similar_question.call_args[1]
        assert called_kwargs["upload"] == upload_with_ocr
        assert called_kwargs["question_index"] == 1


class TestSolverUnavailable:
    @patch("backend.apps.practice.views.PracticeService")
    def test_solver_unavailable_returns_503(self, mock_practice_cls, auth_client, source_question):
        mock_practice = MagicMock()
        mock_practice.generate_similar_question.side_effect = RuntimeError("Provider down")
        mock_practice_cls.return_value = mock_practice

        response = auth_client.post("/api/practice/generate/", {"question_id": source_question.id}, format="json")
        assert response.status_code == 503


class TestInvalidInput:
    def test_missing_context_returns_400(self, auth_client):
        response = auth_client.post("/api/practice/generate/", {}, format="json")
        assert response.status_code == 400

    def test_upload_without_index_returns_400(self, auth_client):
        response = auth_client.post("/api/practice/generate/", {"upload_id": 1}, format="json")
        assert response.status_code == 400

    def test_conflicting_sources_returns_400(self, auth_client, source_question):
        response = auth_client.post("/api/practice/generate/", {"question_id": source_question.id, "upload_id": 1}, format="json")
        assert response.status_code == 400
