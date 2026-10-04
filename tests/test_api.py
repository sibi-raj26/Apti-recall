import pytest
from rest_framework.test import APIClient
from django.urls import reverse

from backend.apps.users.models import User, UserProfile
from backend.apps.topics.models import Topic, Subtopic, ProblemType, Formula
from backend.apps.questions.models import Question, SolutionStep, Shortcut, UploadedQuestion
from backend.apps.solve.models import UserAttempt, VerificationRecord
from backend.apps.recall.models import RecallRecord
from backend.apps.voice.models import VoiceExplanation


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="test@example.com", username="testuser", password="testpass123")


@pytest.fixture
def topic(db):
    return Topic.objects.create(name="Percentage", slug="percentage", order=1)


@pytest.fixture
def subtopic(db, topic):
    return Subtopic.objects.create(topic=topic, name="Basic Percentage", order=1)


@pytest.fixture
def problem_type(db, topic, subtopic):
    return ProblemType.objects.create(topic=topic, subtopic=subtopic, name="percentage-change")


@pytest.fixture
def formula(db, topic, problem_type):
    return Formula.objects.create(topic=topic, problem_type=problem_type, name="Percentage Change", formula_latex=r"\frac{New-Old}{Old} \times 100")


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


@pytest.fixture
def uploaded_question(db, user, topic, problem_type):
    return UploadedQuestion.objects.create(user=user, image="uploads/questions/test.png", detected_topic=topic, detected_problem_type=problem_type)


@pytest.fixture
def user_attempt(db, user, question):
    return UserAttempt.objects.create(user=user, question=question, status="completed", is_correct=True, time_taken_seconds=15)


@pytest.fixture
def verification_record(db, user_attempt):
    return VerificationRecord.objects.create(attempt=user_attempt, method="algebraic", input_data={}, expected_result="30", actual_result="30", is_verified=True)


@pytest.fixture
def recall_record(db, user, topic, problem_type, question):
    return RecallRecord.objects.create(user=user, topic=topic, problem_type=problem_type, question=question, recall_score=0.8, accuracy_score=1.0)


@pytest.fixture
def voice_explanation(db, question, user_attempt):
    return VoiceExplanation.objects.create(question=question, attempt=user_attempt, audio_file="audio/explanations/test.mp3", text_content="Explanation text", language="en", duration_seconds=30)


class TestUserModel:
    def test_create_user(self, db):
        user = User.objects.create_user(email="new@example.com", username="newuser", password="pass123")
        assert user.email == "new@example.com"
        assert user.check_password("pass123")

    def test_user_profile_created(self, user):
        from backend.apps.users.models import UserProfile
        profile = UserProfile.objects.create(user=user)
        assert profile is not None
        assert profile.overall_accuracy == 0.0


class TestTopicModel:
    def test_topic_creation(self, topic):
        assert topic.name == "Percentage"
        assert topic.slug == "percentage"

    def test_topic_unique_name(self, db, topic):
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Topic.objects.create(name="Percentage", slug="percentage-2")

    def test_subtopic_creation(self, subtopic):
        assert subtopic.name == "Basic Percentage"
        assert subtopic.topic_id == subtopic.topic.id


class TestQuestionModel:
    def test_question_creation(self, question):
        assert question.difficulty == "easy"
        assert question.topic.name == "Percentage"

    def test_solution_step_unique(self, question, solution_step):
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            SolutionStep.objects.create(question=question, step_number=1, title="Duplicate", description="...")


class TestHealthEndpoint:
    def test_health(self, api_client):
        response = api_client.get("/api/health/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == "AptiRecall API"


class TestTopicAPI:
    def test_list_topics(self, api_client, topic):
        response = api_client.get("/api/topics/")
        assert response.status_code == 200
        assert response.data["success"] is True
        assert len(response.data["data"]) >= 1

    def test_topic_detail(self, api_client, topic):
        response = api_client.get(f"/api/topics/{topic.id}/")
        assert response.status_code == 200
        assert response.data["data"]["name"] == "Percentage"

    def test_topic_problem_types(self, api_client, topic, problem_type):
        response = api_client.get(f"/api/topics/{topic.id}/problem-types/")
        assert response.status_code == 200
        assert len(response.data["data"]) >= 1

    def test_topic_formulas(self, api_client, topic, formula):
        response = api_client.get(f"/api/topics/{topic.id}/formulas/")
        assert response.status_code == 200
        assert len(response.data["data"]) >= 1


class TestQuestionAPI:
    def test_list_questions(self, api_client, question):
        response = api_client.get("/api/questions/")
        assert response.status_code == 200
        assert response.data["success"] is True
        assert len(response.data["data"]) >= 1

    def test_question_detail(self, api_client, question):
        response = api_client.get(f"/api/questions/{question.id}/")
        assert response.status_code == 200
        assert response.data["data"]["difficulty"] == "easy"

    def test_question_solution(self, api_client, question, solution_step):
        response = api_client.get(f"/api/questions/{question.id}/solution/")
        assert response.status_code == 200
        assert len(response.data["data"]) >= 1

    def test_question_shortcut(self, api_client, question, shortcut):
        response = api_client.get(f"/api/questions/{question.id}/shortcut/")
        assert response.status_code == 200
        assert len(response.data["data"]) >= 1

    def test_question_filter_by_topic(self, api_client, question, topic):
        response = api_client.get(f"/api/questions/?topic={topic.id}")
        assert response.status_code == 200
        assert len(response.data["data"]) >= 1

    def test_question_filter_by_difficulty(self, api_client, question):
        response = api_client.get("/api/questions/?difficulty=easy")
        assert response.status_code == 200
        for q in response.data["data"]:
            assert q["difficulty"] == "easy"

    def test_question_search(self, api_client, question):
        response = api_client.get("/api/questions/?search=20%")
        assert response.status_code == 200

    def test_question_pagination(self, api_client, question):
        response = api_client.get("/api/questions/?page=1")
        assert response.status_code == 200
        assert "meta" in response.data
        assert "page" in response.data["meta"]
        assert "total_count" in response.data["meta"]
