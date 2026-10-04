import pytest
from rest_framework.test import APIClient
from rest_framework import status

from backend.apps.topics.models import Topic, Subtopic, ProblemType, Formula
from backend.apps.users.models import User


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="topicapi@example.com",
        username="topicapi",
        password="topicapipass123",
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
    return Topic.objects.create(name="SeedTopic", slug="seed-topic", description="A seed topic", order=99)


@pytest.fixture
def subtopic(db, topic):
    return Subtopic.objects.create(topic=topic, name="SeedSubtopic", description="A seed subtopic", order=1)


@pytest.fixture
def problem_type(db, topic):
    return ProblemType.objects.create(topic=topic, name="SeedProblemType", description="A seed problem type")


@pytest.fixture
def formula(db, topic, problem_type):
    return Formula.objects.create(topic=topic, problem_type=problem_type, name="SeedFormula", formula_latex="a=b")


class TestTopicListAPI:
    def test_list_topics_requires_auth(self, api_client):
        response = api_client.get("/api/topics/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_topics_authenticated(self, auth_client):
        response = auth_client.get("/api/topics/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["success"] is True
        assert "data" in data
        assert "meta" in data

    def test_list_topics_pagination(self, auth_client):
        response = auth_client.get("/api/topics/?page=1")
        assert response.status_code == status.HTTP_200_OK
        assert "meta" in response.data

    def test_list_topics_filter_is_active(self, auth_client, topic):
        topic.is_active = False
        topic.save()
        response = auth_client.get("/api/topics/?is_active=true")
        assert response.status_code == status.HTTP_200_OK
        slugs = [t["slug"] for t in response.data["data"]]
        assert "seed-topic" not in slugs

    def test_list_topics_search(self, auth_client, topic):
        response = auth_client.get("/api/topics/?search=SeedTopic")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["meta"]["total_count"] >= 1

    def test_list_topics_ordering(self, auth_client):
        response = auth_client.get("/api/topics/?ordering=name")
        assert response.status_code == status.HTTP_200_OK


class TestTopicDetailAPI:
    def test_get_topic_detail(self, auth_client, topic):
        response = auth_client.get(f"/api/topics/{topic.id}/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert data["name"] == topic.name

    def test_get_topic_detail_inactive(self, auth_client, topic):
        topic.is_active = False
        topic.save()
        response = auth_client.get(f"/api/topics/{topic.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_topic_detail_not_found(self, auth_client):
        response = auth_client.get("/api/topics/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTopicSubtopicsAPI:
    def test_get_topic_subtopics(self, auth_client, topic, subtopic):
        response = auth_client.get(f"/api/topics/{topic.id}/subtopics/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert len(data) == 1
        assert data[0]["name"] == subtopic.name

    def test_get_topic_subtopics_inactive_topic(self, auth_client, topic, subtopic):
        topic.is_active = False
        topic.save()
        response = auth_client.get(f"/api/topics/{topic.id}/subtopics/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTopicProblemTypesAPI:
    def test_get_topic_problem_types(self, auth_client, topic, problem_type):
        response = auth_client.get(f"/api/topics/{topic.id}/problem-types/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert len(data) >= 1
        assert data[0]["name"] == problem_type.name

    def test_get_topic_problem_types_inactive_topic(self, auth_client, topic):
        topic.is_active = False
        topic.save()
        response = auth_client.get(f"/api/topics/{topic.id}/problem-types/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTopicFormulasAPI:
    def test_get_topic_formulas(self, auth_client, topic, formula):
        response = auth_client.get(f"/api/topics/{topic.id}/formulas/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert len(data) >= 1
        assert data[0]["name"] == formula.name

    def test_get_topic_formulas_inactive_topic(self, auth_client, topic):
        topic.is_active = False
        topic.save()
        response = auth_client.get(f"/api/topics/{topic.id}/formulas/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
