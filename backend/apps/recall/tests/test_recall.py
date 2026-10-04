import logging
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

from backend.apps.users.models import User
from backend.apps.topics.models import Topic, ProblemType
from backend.apps.questions.models import Question
from backend.apps.solve.models import UserAttempt
from backend.apps.recall.models import RecallRecord
from backend.apps.recall.services.recall_service import (
    compute_recall_score,
    detect_weakness,
    update_recall,
    get_daily_queue,
    get_weak_topics,
    get_recall_analytics,
    RECALL_STRONG_THRESHOLD,
    RECALL_MODERATE_THRESHOLD,
)

logger = logging.getLogger(__name__)


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="recalluser@example.com", username="recalluser", password="recallpass123")


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
def problem_type(db, topic):
    return ProblemType.objects.create(topic=topic, name="percentage-basic")


@pytest.fixture
def question(db, topic, problem_type, user):
    return Question.objects.create(
        topic=topic,
        problem_type=problem_type,
        difficulty="easy",
        question_text="What is 20% of 150?",
        correct_answer="30",
        explanation_concept="Percentage means per hundred.",
        explanation_approach="Multiply.",
        explanation_steps=[],
        is_active=True,
        created_by=user,
    )


class TestRecallScoreComputation:
    def test_correct_attempt_produces_higher_score(self, question, user):
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
        score = compute_recall_score(attempt)
        assert score >= 0.0
        assert score <= 1.0

    def test_incorrect_attempt_produces_lower_score(self, question, user):
        attempt = UserAttempt.objects.create(
            user=user,
            question=question,
            status="completed",
            is_correct=False,
            hints_used=0,
            attempts_count=1,
            time_taken_seconds=20,
            viewed_solution=False,
            viewed_shortcut=False,
        )
        score = compute_recall_score(attempt)
        assert score >= 0.0
        assert score <= 1.0

    def test_viewed_solution_penalty(self, question, user):
        attempt = UserAttempt.objects.create(
            user=user,
            question=question,
            status="completed",
            is_correct=True,
            hints_used=0,
            attempts_count=1,
            time_taken_seconds=20,
            viewed_solution=True,
            viewed_shortcut=False,
        )
        score_with_penalty = compute_recall_score(attempt)
        attempt.viewed_solution = False
        score_without_penalty = compute_recall_score(attempt)
        assert score_with_penalty < score_without_penalty

    def test_score_clamped_to_valid_range(self, question, user):
        attempt = UserAttempt.objects.create(
            user=user,
            question=question,
            status="completed",
            is_correct=False,
            hints_used=5,
            attempts_count=5,
            time_taken_seconds=10000,
            viewed_solution=True,
            viewed_shortcut=True,
        )
        score = compute_recall_score(attempt)
        assert score >= 0.0
        assert score <= 1.0


class TestWeaknessDetection:
    def test_consecutive_incorrect_detected_as_weak(self, question, user):
        for _ in range(3):
            UserAttempt.objects.create(
                user=user,
                question=question,
                status="completed",
                is_correct=False,
                hints_used=0,
                attempts_count=1,
            )
        record = RecallRecord.objects.create(user=user, topic=question.topic, problem_type=question.problem_type, question=question)
        recent = UserAttempt.objects.filter(user=user, question=question, status="completed").order_by("-created_at")[:20]
        assert detect_weakness(record, list(recent)) is True

    def test_all_correct_not_weak(self, question, user):
        for _ in range(3):
            UserAttempt.objects.create(
                user=user,
                question=question,
                status="completed",
                is_correct=True,
                hints_used=0,
                attempts_count=1,
            )
        record = RecallRecord.objects.create(user=user, topic=question.topic, problem_type=question.problem_type, question=question)
        recent = UserAttempt.objects.filter(user=user, question=question, status="completed").order_by("-created_at")[:20]
        assert detect_weakness(record, list(recent)) is False


class TestRecallRecordUpdate:
    def test_creates_recall_record(self, question, user):
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
        record = update_recall(user, attempt)
        assert record.user == user
        assert record.topic == question.topic
        assert record.problem_type == question.problem_type
        assert record.question == question
        assert record.practice_count == 1
        assert record.last_practiced is not None

    def test_updates_existing_recall_record(self, question, user):
        attempt1 = UserAttempt.objects.create(
            user=user,
            question=question,
            status="completed",
            is_correct=True,
            hints_used=0,
            attempts_count=1,
        )
        record = update_recall(user, attempt1)
        initial_count = record.practice_count

        attempt2 = UserAttempt.objects.create(
            user=user,
            question=question,
            status="completed",
            is_correct=False,
            hints_used=0,
            attempts_count=1,
        )
        record.refresh_from_db()
        update_recall(user, attempt2)
        record.refresh_from_db()
        assert record.practice_count == initial_count + 1


class TestDailyQueue:
    def test_returns_due_records(self, user, topic, problem_type, question):
        record = RecallRecord.objects.create(
            user=user,
            topic=topic,
            problem_type=problem_type,
            question=question,
            next_practice_at=timezone.now() - timedelta(days=1),
        )
        queue = get_daily_queue(user)
        assert record in queue

    def test_excludes_future_records(self, user, topic, problem_type, question):
        record = RecallRecord.objects.create(
            user=user,
            topic=topic,
            problem_type=problem_type,
            question=question,
            next_practice_at=timezone.now() + timedelta(days=7),
        )
        queue = get_daily_queue(user)
        assert record not in queue


class TestWeakTopics:
    def test_returns_weak_records(self, user, topic, problem_type, question):
        weak_record = RecallRecord.objects.create(user=user, topic=topic, problem_type=problem_type, question=question, is_weak=True)
        strong_question = Question.objects.create(
            topic=topic,
            problem_type=problem_type,
            difficulty="easy",
            question_text="What is 10% of 100?",
            correct_answer="10",
            explanation_concept="Percentage",
            explanation_approach="Multiply.",
            explanation_steps=[],
            is_active=True,
            created_by=user,
        )
        strong_record = RecallRecord.objects.create(
            user=user,
            topic=topic,
            problem_type=problem_type,
            question=strong_question,
            is_weak=False,
            recall_score=0.9,
        )
        weak_topics = get_weak_topics(user)
        assert weak_record in weak_topics
        assert strong_record not in weak_topics


class TestAnalytics:
    def test_returns_correct_counts(self, user, topic, problem_type, question):
        strong_question = Question.objects.create(
            topic=topic,
            problem_type=problem_type,
            difficulty="easy",
            question_text="What is 10% of 100?",
            correct_answer="10",
            explanation_concept="Percentage",
            explanation_approach="Multiply.",
            explanation_steps=[],
            is_active=True,
            created_by=user,
        )
        weak_question = Question.objects.create(
            topic=topic,
            problem_type=problem_type,
            difficulty="easy",
            question_text="What is 5% of 200?",
            correct_answer="10",
            explanation_concept="Percentage",
            explanation_approach="Multiply.",
            explanation_steps=[],
            is_active=True,
            created_by=user,
        )
        RecallRecord.objects.create(user=user, topic=topic, problem_type=problem_type, question=strong_question, recall_score=0.9, is_weak=False)
        RecallRecord.objects.create(user=user, topic=topic, problem_type=problem_type, question=weak_question, recall_score=0.3, is_weak=True)
        analytics = get_recall_analytics(user)
        assert analytics["total_topics"] == 2
        assert analytics["weak_count"] == 1
        assert analytics["strong_count"] == 1


class TestUnauthenticatedRejected:
    def test_unauthenticated_schedule_rejected(self, api_client):
        response = api_client.get("/api/recall/schedule/")
        assert response.status_code == 401

    def test_unauthenticated_weak_topics_rejected(self, api_client):
        response = api_client.get("/api/recall/weak-topics/")
        assert response.status_code == 401

    def test_unauthenticated_analytics_rejected(self, api_client):
        response = api_client.get("/api/recall/analytics/")
        assert response.status_code == 401


class TestScheduleAPI:
    def test_schedule_returns_empty_when_no_records(self, auth_client):
        response = auth_client.get("/api/recall/schedule/")
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_schedule_returns_due_records(self, auth_client, user, topic, problem_type, question):
        from django.utils import timezone
        from datetime import timedelta
        record = RecallRecord.objects.create(
            user=user,
            topic=topic,
            problem_type=problem_type,
            question=question,
            next_practice_at=timezone.now() - timedelta(days=1),
        )
        response = auth_client.get("/api/recall/schedule/")
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1


class TestSubmitAPI:
    def test_submit_creates_recall_record(self, auth_client, user, question):
        attempt = UserAttempt.objects.create(
            user=user,
            question=question,
            status="completed",
            is_correct=True,
            hints_used=0,
            attempts_count=1,
        )
        response = auth_client.post("/api/recall/submit/", {"attempt_id": attempt.id}, format="json")
        assert response.status_code == 200
        assert response.json()["data"]["practice_count"] == 1

    def test_submit_requires_completed_attempt(self, auth_client, user, question):
        attempt = UserAttempt.objects.create(
            user=user,
            question=question,
            status="in_progress",
        )
        response = auth_client.post("/api/recall/submit/", {"attempt_id": attempt.id}, format="json")
        assert response.status_code == 404


class TestWeakTopicsAPI:
    def test_weak_topics_returns_empty_when_none(self, auth_client):
        response = auth_client.get("/api/recall/weak-topics/")
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_weak_topics_returns_weak_only(self, auth_client, user, topic, problem_type, question):
        strong_question = Question.objects.create(
            topic=topic,
            problem_type=problem_type,
            difficulty="easy",
            question_text="What is 10% of 100?",
            correct_answer="10",
            explanation_concept="Percentage",
            explanation_approach="Multiply.",
            explanation_steps=[],
            is_active=True,
            created_by=user,
        )
        RecallRecord.objects.create(user=user, topic=topic, problem_type=problem_type, question=question, is_weak=True)
        RecallRecord.objects.create(user=user, topic=topic, problem_type=problem_type, question=strong_question, is_weak=False, recall_score=0.9)
        response = auth_client.get("/api/recall/weak-topics/")
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1


class TestAnalyticsAPI:
    def test_analytics_returns_correct_data(self, auth_client, user, topic, problem_type, question):
        RecallRecord.objects.create(user=user, topic=topic, problem_type=problem_type, question=question, recall_score=0.9, is_weak=False)
        response = auth_client.get("/api/recall/analytics/")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_topics"] == 1
        assert data["strong_count"] == 1
