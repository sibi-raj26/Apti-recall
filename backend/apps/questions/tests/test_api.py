import pytest
from rest_framework.test import APIClient
from rest_framework import status

from backend.apps.questions.models import Question, SolutionStep, Shortcut
from backend.apps.topics.models import Topic, Subtopic, ProblemType
from backend.apps.users.models import User


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="qapi@example.com",
        username="qapi",
        password="qapipass123",
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
    return Topic.objects.create(name="QAPITopic", slug="qa-pi-topic", description="QA topic", order=98)


@pytest.fixture
def subtopic(db, topic):
    return Subtopic.objects.create(topic=topic, name="QASubtopic", description="QA subtopic", order=1)


@pytest.fixture
def problem_type(db, topic):
    return ProblemType.objects.create(topic=topic, name="QAProblemType", description="QA problem type")


@pytest.fixture
def question(db, topic, problem_type, user):
    return Question.objects.create(
        topic=topic,
        problem_type=problem_type,
        difficulty="easy",
        question_text="What is 5 + 3?",
        correct_answer="8",
        explanation_concept="Basic addition.",
        explanation_approach="Add the two numbers.",
        explanation_steps=[],
        is_active=True,
        created_by=user,
    )


@pytest.fixture
def inactive_question(db, topic, problem_type, user):
    return Question.objects.create(
        topic=topic,
        problem_type=problem_type,
        difficulty="easy",
        question_text="This should not appear.",
        correct_answer="secret",
        explanation_concept="Concept.",
        explanation_approach="Approach.",
        explanation_steps=[],
        is_active=False,
        created_by=user,
    )


class TestQuestionListAPI:
    def test_list_questions_requires_auth(self, api_client):
        response = api_client.get("/api/questions/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_questions_authenticated(self, auth_client):
        response = auth_client.get("/api/questions/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["success"] is True
        assert "data" in data
        assert "meta" in data

    def test_list_questions_excludes_inactive(self, auth_client, question, inactive_question):
        response = auth_client.get("/api/questions/")
        assert response.status_code == status.HTTP_200_OK
        texts = [q["question_text"] for q in response.data["data"]]
        assert "This should not appear." not in texts

    def test_list_questions_filter_topic(self, auth_client, question, topic):
        response = auth_client.get(f"/api/questions/?topic={topic.id}")
        assert response.status_code == status.HTTP_200_OK
        for q in response.data["data"]:
            assert q["topic"] == topic.id

    def test_list_questions_filter_problem_type(self, auth_client, question, problem_type):
        response = auth_client.get(f"/api/questions/?problem_type={problem_type.id}")
        assert response.status_code == status.HTTP_200_OK
        for q in response.data["data"]:
            assert q["problem_type"] == problem_type.id

    def test_list_questions_filter_difficulty(self, auth_client, question):
        response = auth_client.get(f"/api/questions/?difficulty=easy")
        assert response.status_code == status.HTTP_200_OK
        for q in response.data["data"]:
            assert q["difficulty"] == "easy"

    def test_list_questions_filter_search(self, auth_client, question):
        response = auth_client.get("/api/questions/?search=5")
        assert response.status_code == status.HTTP_200_OK
        texts = [q["question_text"] for q in response.data["data"]]
        assert any("5" in t for t in texts)

    def test_list_questions_ordering(self, auth_client):
        response = auth_client.get("/api/questions/?ordering=created_at")
        assert response.status_code == status.HTTP_200_OK

    def test_list_questions_pagination(self, auth_client):
        response = auth_client.get("/api/questions/?page=1")
        assert response.status_code == status.HTTP_200_OK
        assert "meta" in response.data


class TestQuestionDetailAPI:
    def test_get_question_detail(self, auth_client, question):
        response = auth_client.get(f"/api/questions/{question.id}/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert data["question_text"] == question.question_text
        assert data["correct_answer"] == question.correct_answer

    def test_get_question_detail_inactive(self, auth_client, inactive_question):
        response = auth_client.get(f"/api/questions/{inactive_question.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_question_detail_not_found(self, auth_client):
        response = auth_client.get("/api/questions/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestQuestionSolutionAPI:
    def test_get_question_solution(self, auth_client, question):
        step = SolutionStep.objects.create(question=question, step_number=1, title="Step 1", description="Add numbers")
        response = auth_client.get(f"/api/questions/{question.id}/solution/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert len(data) == 1
        assert data[0]["step_number"] == 1

    def test_get_question_solution_inactive(self, auth_client, inactive_question):
        response = auth_client.get(f"/api/questions/{inactive_question.id}/solution/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_question_solution_not_found(self, auth_client):
        response = auth_client.get("/api/questions/99999/solution/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestQuestionShortcutAPI:
    def test_get_question_shortcut(self, auth_client, question):
        Shortcut.objects.create(question=question, title="Quick Add", description="5+3=8", formula="", example="")
        response = auth_client.get(f"/api/questions/{question.id}/shortcut/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert len(data) == 1
        assert data[0]["title"] == "Quick Add"

    def test_get_question_shortcut_no_shortcut(self, auth_client, question):
        response = auth_client.get(f"/api/questions/{question.id}/shortcut/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"] == []

    def test_get_question_shortcut_inactive(self, auth_client, inactive_question):
        response = auth_client.get(f"/api/questions/{inactive_question.id}/shortcut/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_question_shortcut_not_found(self, auth_client):
        response = auth_client.get("/api/questions/99999/shortcut/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestQuestionStubEndpoints:
    def test_attempt_stub(self, auth_client, question):
        response = auth_client.post(f"/api/questions/{question.id}/attempt/", {}, format="json")
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED

    def test_similar_stub(self, auth_client, question):
        response = auth_client.get(f"/api/questions/{question.id}/similar/")
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED

    def test_hint_stub(self, auth_client, question):
        response = auth_client.post(f"/api/questions/{question.id}/hint/", {}, format="json")
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
