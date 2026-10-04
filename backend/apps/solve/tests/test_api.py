import pytest
from unittest.mock import MagicMock, patch

from rest_framework.test import APIClient
from rest_framework import status

from backend.apps.solve.models import UserAttempt
from backend.apps.solve.services.solver_service import SolveService
from backend.apps.users.models import User
from backend.apps.topics.models import Topic, ProblemType
from backend.apps.questions.models import Question


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="solveapi@example.com",
        username="solveapi",
        password="solveapipass123",
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def topic(db):
    return Topic.objects.create(name="SolveTopic", slug="solve-topic", description="Solve topic", order=97)


@pytest.fixture
def problem_type(db, topic):
    return ProblemType.objects.create(topic=topic, name="SolvePT", description="Solve problem type")


@pytest.fixture
def question(db, topic, problem_type, user):
    return Question.objects.create(
        topic=topic,
        problem_type=problem_type,
        difficulty="easy",
        question_text="What is 2 + 2?",
        correct_answer="4",
        explanation_concept="Addition",
        explanation_approach="Add",
        explanation_steps=[],
        is_active=True,
        created_by=user,
    )


class TestSolveTextAPI:
    def test_solve_requires_auth(self, api_client):
        response = api_client.post("/api/solve/text/", {"question_text": "2+2?"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_solve_empty_body_returns_400(self, auth_client):
        response = auth_client.post("/api/solve/text/", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_solve_empty_question_returns_400(self, auth_client):
        response = auth_client.post("/api/solve/text/", {"question_text": ""}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_solve_whitespace_question_returns_400(self, auth_client):
        response = auth_client.post("/api/solve/text/", {"question_text": "   "}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_solve_too_long_question_returns_400(self, auth_client):
        response = auth_client.post("/api/solve/text/", {"question_text": "a" * 5001}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_solve_existing_question(self, auth_client, question):
        response = auth_client.post("/api/solve/text/", {"question_text": "What is 2 + 2?"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert data["source"] == "existing"
        assert data["final_answer"] == "4"
        assert data["verification_status"] == "NOT_VERIFIED"
        assert data["attempt_id"] is not None
        assert UserAttempt.objects.filter(id=data["attempt_id"]).exists()

    def test_solve_unseen_question_mocked(self, auth_client):
        mock_service = MagicMock()
        mock_service.solve.return_value = {
            "question_text": "What is 7 + 35?",
            "topic": {"id": 1, "name": "Number System"},
            "problem_type": {"id": 1, "name": "Basic Arithmetic"},
            "concept": "Basic addition",
            "approach": "Add the two numbers.",
            "steps": [{"step": 1, "title": "Add", "calculation": "7 + 35 = 42", "explanation": "Sum the numbers."}],
            "final_answer": "42",
            "shortcut": "",
            "confidence": 0.85,
            "verification_status": "NOT_VERIFIED",
            "source": "ai_generated",
            "attempt_id": 999,
        }
        with patch("backend.apps.solve.views.SolveService", return_value=mock_service):
            response = auth_client.post("/api/solve/text/", {"question_text": "What is 7 + 35?"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert data["source"] == "ai_generated"
        assert data["final_answer"] == "42"
        assert data["verification_status"] == "NOT_VERIFIED"
        assert data["confidence"] == 0.85
        assert mock_service.solve.called

    def test_solve_creates_user_attempt(self, auth_client, user, question):
        response = auth_client.post("/api/solve/text/", {"question_text": "What is 2 + 2?"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        attempt_id = response.data["data"]["attempt_id"]
        attempt = UserAttempt.objects.get(id=attempt_id)
        assert attempt.user == user
        assert attempt.question == question
        assert attempt.status == "completed"

    def test_solve_returns_503_when_ai_unavailable(self, auth_client):
        mock_service = MagicMock()
        mock_service.solve.side_effect = RuntimeError("Provider down")
        with patch("backend.apps.solve.views.SolveService", return_value=mock_service):
            response = auth_client.post("/api/solve/text/", {"question_text": "A truly unique question xyz?"}, format="json")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data["error"]["code"] == "AI_UNAVAILABLE"

    def test_solve_does_not_expose_api_key_on_error(self, auth_client):
        mock_service = MagicMock()
        mock_service.solve.side_effect = RuntimeError("Provider down")
        with patch("backend.apps.solve.views.SolveService", return_value=mock_service):
            response = auth_client.post("/api/solve/text/", {"question_text": "A unique question abc?"}, format="json")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        response_str = str(response.data).lower()
        assert "api_key" not in response_str
        assert "openai_api_key" not in response_str
        assert "traceback" not in response_str


class TestSolveHistoryAPI:
    def test_history_requires_auth(self, api_client):
        response = api_client.get("/api/solve/history/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_history_authenticated_empty(self, auth_client):
        response = auth_client.get("/api/solve/history/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"] == []
        assert response.data["meta"]["total_count"] == 0

    def test_history_returns_attempts(self, auth_client, user, question):
        attempt = UserAttempt.objects.create(user=user, question=question, status="completed")
        response = auth_client.get("/api/solve/history/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 1
        assert response.data["data"][0]["id"] == attempt.id

    def test_history_pagination(self, auth_client, user, question):
        for i in range(5):
            UserAttempt.objects.create(user=user, question=question, status="completed")
        response = auth_client.get("/api/solve/history/?page=1")
        assert response.status_code == status.HTTP_200_OK
        assert "meta" in response.data
        assert response.data["meta"]["total_count"] == 5


class TestVerifyAnswerStub:
    def test_verify_returns_200(self, auth_client, user):
        attempt = UserAttempt.objects.create(user=user, status="completed", solution_feedback={})
        response = auth_client.post("/api/solve/verify/", {"attempt_id": attempt.id}, format="json")
        assert response.status_code == status.HTTP_200_OK
