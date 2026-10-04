import pytest
from unittest.mock import MagicMock, patch
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from backend.apps.users.models import User
from backend.apps.topics.models import Topic, Subtopic, ProblemType, Formula
from backend.apps.questions.models import Question, SolutionStep, Shortcut, UploadedQuestion
from backend.apps.solve.models import UserAttempt
from backend.apps.recall.models import RecallRecord


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="crossplatform@example.com",
        username="crossplatformuser",
        password="crossplatformpass123",
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def topic(db):
    return Topic.objects.create(name="Percentage", slug="percentage", order=1)


@pytest.fixture
def subtopic(db, topic):
    return Subtopic.objects.create(topic=topic, name="Basic Percentage", order=1)


@pytest.fixture
def problem_type(db, topic, subtopic):
    return ProblemType.objects.create(topic=topic, subtopic=subtopic, name="percentage-basic")


@pytest.fixture
def formula(db, topic, problem_type):
    return Formula.objects.create(
        topic=topic,
        problem_type=problem_type,
        name="Percentage Change",
        formula_latex=r"\frac{New-Old}{Old} \times 100",
    )


@pytest.fixture
def question(db, topic, problem_type, user):
    return Question.objects.create(
        topic=topic,
        problem_type=problem_type,
        difficulty="easy",
        question_text="What is 20% of 150?",
        correct_answer="30",
        explanation_concept="Percentage means per hundred.",
        explanation_approach="Multiply the number by the percentage divided by 100.",
        explanation_steps=["Step 1: 20/100 = 0.2", "Step 2: 150 * 0.2 = 30"],
        hints=["Think of 20% as 20/100"],
        tags=["basic", "percentage"],
        created_by=user,
    )


class TestCrossPlatformConsistency:
    def test_topics_api_returns_consistent_structure(self, auth_client, topic, subtopic, problem_type, formula):
        response = auth_client.get("/api/topics/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "data" in response.data
        assert len(response.data["data"]) >= 1

        detail = auth_client.get(f"/api/topics/{topic.id}/")
        assert detail.status_code == status.HTTP_200_OK
        topic_data = detail.data["data"]
        assert "subtopics" in topic_data
        assert "problem_types" in topic_data
        assert "formulas" in topic_data

    def test_questions_api_returns_consistent_structure(self, auth_client, question, topic, problem_type):
        response = auth_client.get("/api/questions/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "data" in response.data

        detail = auth_client.get(f"/api/questions/{question.id}/")
        assert detail.status_code == status.HTTP_200_OK
        q_data = detail.data["data"]
        assert q_data["correct_answer"] == "30"
        assert "solution_steps" in q_data
        assert "shortcuts" in q_data

    def test_solve_api_returns_consistent_response(self, auth_client, question):
        response = auth_client.post("/api/solve/text/", {"question_text": question.question_text}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert "final_answer" in data
        assert "steps" in data
        assert "verification_status" in data
        assert data["verification_status"] in {"VERIFIED", "FAILED", "UNABLE_TO_VERIFY", "NOT_VERIFIED"}

    def test_recall_api_returns_consistent_structure(self, auth_client, question, user):
        RecallRecord.objects.create(
            user=user,
            topic=question.topic,
            problem_type=question.problem_type,
            question=question,
            recall_score=0.8,
            accuracy_score=1.0,
            practice_count=1,
            last_practiced=None,
            next_practice_at=None,
            difficulty_at_practice="easy",
            is_weak=False,
        )
        schedule = auth_client.get("/api/recall/schedule/")
        assert schedule.status_code == status.HTTP_200_OK
        assert schedule.data["success"] is True

        analytics = auth_client.get("/api/recall/analytics/")
        assert analytics.status_code == status.HTTP_200_OK
        assert analytics.data["success"] is True
        assert "total_topics" in analytics.data["data"]

    def test_practice_api_returns_consistent_structure(self, auth_client, question):
        with patch("backend.apps.practice.views.PracticeService") as mock_practice_cls:
            mock_practice = MagicMock()
            mock_practice.generate_similar_question.return_value = {
                "question_text": "What is 25% of 200?",
                "topic": {"id": question.topic_id, "name": question.topic.name},
                "problem_type": {"id": question.problem_type_id, "name": question.problem_type.name},
                "difficulty": "easy",
                "concept": "Percentage concept.",
                "approach": "Multiply.",
                "steps": [],
                "final_answer": "50",
                "shortcut": "",
                "confidence": 0.9,
                "verification_status": "VERIFIED",
                "verification_details": {},
                "source": "generated",
                "attempt": 1,
            }
            mock_practice_cls.return_value = mock_practice

            response = auth_client.post("/api/practice/generate/", {"question_id": question.id}, format="json")
            assert response.status_code == status.HTTP_200_OK
            assert response.data["success"] is True

    def test_auth_api_returns_consistent_response(self, api_client):
        response = api_client.post("/api/auth/login/", {"email": "nonexistent@example.com", "password": "wrongpass"}, format="json")
        assert response.status_code in {status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED}
        assert response.data["success"] is False
        assert "error" in response.data

    def test_upload_api_returns_consistent_structure(self, auth_client, user, topic, problem_type):
        import io
        from PIL import Image as PILImage
        from unittest.mock import MagicMock, patch
        from backend.apps.upload.services.image_preprocessor import PreprocessedImage
        from backend.ai_services.ocr.base import OCRResult

        buffer = io.BytesIO()
        image = PILImage.new("RGB", (100, 50), (255, 255, 255))
        image.save(buffer, format="PNG")
        buffer.seek(0)
        buffer.name = "test.png"

        mock_preprocessed = PreprocessedImage(path="/tmp/test.png", width=100, height=50, format="PNG")
        mock_ocr = OCRResult(text="What is 20% of 150?", confidence=0.9, provider="tesseract", language="eng", status="success")

        with patch("backend.apps.upload.views.ImagePreprocessor") as mock_preprocessor_cls, \
             patch("backend.apps.upload.views.OCRService") as mock_ocr_cls:
            mock_preprocessor_cls.return_value = MagicMock(preprocess=MagicMock(return_value=mock_preprocessed))
            mock_ocr_cls.return_value = MagicMock(extract_text=MagicMock(return_value=mock_ocr))

            response = auth_client.post("/api/upload/image/", {"image": buffer}, format="multipart")
            assert response.status_code == status.HTTP_200_OK
            assert response.data["success"] is True
            assert "upload_id" in response.data["data"]
            assert "questions" in response.data["data"]
