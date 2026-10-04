import pytest
from unittest.mock import MagicMock, patch
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from backend.apps.users.models import User, UserProfile
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
        email="integration@example.com",
        username="integrationuser",
        password="integrationpass123",
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


@pytest.fixture
def solution_step(db, question):
    return SolutionStep.objects.create(question=question, step_number=1, title="Calculate fraction", description="20/100 = 0.2")


@pytest.fixture
def shortcut(db, question):
    return Shortcut.objects.create(question=question, title="Quick method", description="Divide by 5 directly.")


class TestEndToEndUserFlow:
    def test_complete_learning_flow(self, auth_client, question, topic, problem_type, subtopic, formula, solution_step, shortcut):
        list_response = auth_client.get("/api/topics/")
        assert list_response.status_code == status.HTTP_200_OK
        assert list_response.data["success"] is True

        detail_response = auth_client.get(f"/api/topics/{topic.id}/")
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["data"]["name"] == "Percentage"

        question_response = auth_client.get("/api/questions/")
        assert question_response.status_code == status.HTTP_200_OK
        assert len(question_response.data["data"]) >= 1

        q_detail = auth_client.get(f"/api/questions/{question.id}/")
        assert q_detail.status_code == status.HTTP_200_OK
        assert q_detail.data["data"]["correct_answer"] == "30"

        solution = auth_client.get(f"/api/questions/{question.id}/solution/")
        assert solution.status_code == status.HTTP_200_OK

        shortcut_resp = auth_client.get(f"/api/questions/{question.id}/shortcut/")
        assert shortcut_resp.status_code == status.HTTP_200_OK

        solve_resp = auth_client.post("/api/solve/text/", {"question_text": question.question_text}, format="json")
        assert solve_resp.status_code == status.HTTP_200_OK
        assert solve_resp.data["success"] is True

    def test_registration_returns_jwt_tokens(self, api_client):
        payload = {
            "email": "e2euser@example.com",
            "username": "e2euser",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        response = api_client.post("/api/auth/register/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.data["data"]
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["email"] == payload["email"]

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {data['access']}")
        me = client.get("/api/auth/me/")
        assert me.status_code == status.HTTP_200_OK
        assert me.data["data"]["email"] == payload["email"]

    def test_login_flow(self, api_client, user):
        login_resp = api_client.post("/api/auth/login/", {"email": user.email, "password": "integrationpass123"}, format="json")
        assert login_resp.status_code == status.HTTP_200_OK
        tokens = login_resp.data["data"]
        assert "access" in tokens
        assert "refresh" in tokens

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        profile = client.get("/api/auth/profile/")
        assert profile.status_code == status.HTTP_200_OK

        logout_resp = client.post("/api/auth/logout/", {"refresh": tokens["refresh"]}, format="json")
        assert logout_resp.status_code == status.HTTP_200_OK

    def test_refresh_token_flow(self, api_client, user):
        refresh = RefreshToken.for_user(user)
        refresh_resp = api_client.post("/api/auth/refresh/", {"refresh": str(refresh)}, format="json")
        assert refresh_resp.status_code == status.HTTP_200_OK
        assert "access" in refresh_resp.data["data"]

    def test_authenticated_user_can_create_and_complete_attempt(self, auth_client, question):
        solve_resp = auth_client.post("/api/solve/text/", {"question_text": question.question_text}, format="json")
        assert solve_resp.status_code == status.HTTP_200_OK
        attempt_id = solve_resp.data["data"]["attempt_id"]
        assert UserAttempt.objects.filter(id=attempt_id).exists()

        history = auth_client.get("/api/solve/history/")
        assert history.status_code == status.HTTP_200_OK
        assert len(history.data["data"]) >= 1

    def test_uploaded_question_lifecycle(self, auth_client, user, topic, problem_type):
        import io
        from PIL import Image as PILImage

        image = PILImage.new("RGB", (100, 50), (255, 255, 255))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        buffer.name = "test.png"

        upload_resp = auth_client.post("/api/upload/image/", {"image": buffer}, format="multipart")
        assert upload_resp.status_code == status.HTTP_200_OK
        upload_id = upload_resp.data["data"]["upload_id"]
        assert UploadedQuestion.objects.filter(id=upload_id).exists()

        status_resp = auth_client.get(f"/api/upload/{upload_id}/status/")
        assert status_resp.status_code == status.HTTP_200_OK

        result = auth_client.get(f"/api/upload/{upload_id}/result/")
        assert result.status_code == status.HTTP_200_OK

    def test_recall_queue_requires_due_items(self, auth_client, question, user):
        attempt = UserAttempt.objects.create(
            user=user,
            question=question,
            status="completed",
            is_correct=True,
            hints_used=0,
            attempts_count=1,
            time_taken_seconds=20,
            viewed_solution=False,
            viewed_shortcut=False,
        )
        RecallRecord.objects.create(
            user=user,
            topic=question.topic,
            problem_type=question.problem_type,
            question=question,
            recall_score=0.3,
            accuracy_score=1.0,
            practice_count=1,
            last_practiced=None,
            next_practice_at=None,
            difficulty_at_practice="easy",
            is_weak=True,
        )

        schedule = auth_client.get("/api/recall/schedule/")
        assert schedule.status_code == status.HTTP_200_OK
        assert schedule.data["success"] is True

        analytics = auth_client.get("/api/recall/analytics/")
        assert analytics.status_code == status.HTTP_200_OK

    def test_practice_generate_with_existing_question(self, auth_client, question):
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

            practice_resp = auth_client.post("/api/practice/generate/", {"question_id": question.id}, format="json")
            assert practice_resp.status_code == status.HTTP_200_OK
            assert practice_resp.data["success"] is True

    def test_unauthorized_access_to_protected_routes(self, api_client):
        protected_routes = [
            "/api/topics/",
            "/api/questions/",
            "/api/solve/text/",
            "/api/upload/image/",
            "/api/recall/schedule/",
            "/api/practice/generate/",
            "/api/auth/me/",
            "/api/auth/profile/",
        ]
        for route in protected_routes:
            response = api_client.get(route) if "text" not in route and "image" not in route else api_client.post(route, {}, format="json")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, f"Expected 401 for {route}, got {response.status_code}"

    def test_cross_module_data_consistency(self, auth_client, question, user):
        solve_resp = auth_client.post("/api/solve/text/", {"question_text": question.question_text}, format="json")
        assert solve_resp.status_code == status.HTTP_200_OK
        attempt_id = solve_resp.data["data"]["attempt_id"]
        attempt = UserAttempt.objects.get(id=attempt_id)
        assert attempt.question_id == question.id
        assert attempt.user_id == user.id

        recall = RecallRecord.objects.create(
            user=user,
            topic=question.topic,
            problem_type=question.problem_type,
            question=question,
            recall_score=0.5,
            accuracy_score=1.0,
            practice_count=1,
            last_practiced=None,
            next_practice_at=None,
            difficulty_at_practice="easy",
            is_weak=False,
        )
        assert recall.topic_id == question.topic_id
        assert recall.problem_type_id == question.problem_type_id
