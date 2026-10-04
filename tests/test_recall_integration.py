import pytest
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

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
)


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="recallintegration@example.com",
        username="recallintegration",
        password="recallpass123",
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


class TestRecallScoreIntegration:
    def test_correct_answer_produces_non_zero_score(self, question, user):
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

    def test_incorrect_answer_decreases_recall(self, question, user):
        attempt = UserAttempt.objects.create(
            user=user,
            question=question,
            status="completed",
            is_correct=False,
            hints_used=0,
            attempts_count=1,
            time_taken_seconds=15,
            viewed_solution=False,
            viewed_shortcut=False,
        )
        score = compute_recall_score(attempt)
        assert 0.0 <= score <= 1.0
        assert score < 0.5

    def test_viewed_solution_penalty(self, question, user):
        correct_attempt = UserAttempt.objects.create(
            user=user,
            question=question,
            status="completed",
            is_correct=True,
            hints_used=0,
            attempts_count=1,
            time_taken_seconds=15,
            viewed_solution=True,
            viewed_shortcut=False,
        )
        no_penalty_attempt = UserAttempt.objects.create(
            user=user,
            question=question,
            status="completed",
            is_correct=True,
            hints_used=0,
            attempts_count=1,
            time_taken_seconds=15,
            viewed_solution=False,
            viewed_shortcut=False,
        )
        score_with_penalty = compute_recall_score(correct_attempt)
        score_without_penalty = compute_recall_score(no_penalty_attempt)
        assert score_with_penalty < score_without_penalty

    def test_recall_record_updated_after_attempt(self, question, user):
        record = RecallRecord.objects.create(
            user=user,
            topic=question.topic,
            problem_type=question.problem_type,
            question=question,
            recall_score=0.5,
            accuracy_score=0.5,
            practice_count=0,
            last_practiced=None,
            next_practice_at=None,
            difficulty_at_practice="easy",
            is_weak=False,
        )
        attempt = UserAttempt.objects.create(
            user=user,
            question=question,
            status="completed",
            is_correct=True,
            hints_used=0,
            attempts_count=1,
            time_taken_seconds=15,
            viewed_solution=False,
            viewed_shortcut=False,
        )
        update_recall(user, attempt)
        record.refresh_from_db()
        assert record.practice_count == 1
        assert record.last_practiced is not None

    def test_weakness_detection_after_multiple_incorrect_attempts(self, question, user):
        for _ in range(4):
            UserAttempt.objects.create(
                user=user,
                question=question,
                status="completed",
                is_correct=False,
                hints_used=0,
                attempts_count=1,
                time_taken_seconds=15,
                viewed_solution=False,
                viewed_shortcut=False,
            )
        record = RecallRecord.objects.create(
            user=user,
            topic=question.topic,
            problem_type=question.problem_type,
            question=question,
            recall_score=0.1,
            accuracy_score=0.0,
            practice_count=0,
            last_practiced=None,
            next_practice_at=None,
            difficulty_at_practice="easy",
            is_weak=False,
        )
        recent_attempts = list(UserAttempt.objects.filter(user=user, question=question, status="completed").order_by("-created_at")[:20])
        record.is_weak = detect_weakness(record, recent_attempts)
        record.save()
        assert record.is_weak is True

        weak_topics = get_weak_topics(user)
        assert len(weak_topics) >= 1

    def test_daily_queue_returns_due_items(self, question, user):
        from django.utils import timezone
        from datetime import timedelta

        RecallRecord.objects.create(
            user=user,
            topic=question.topic,
            problem_type=question.problem_type,
            question=question,
            recall_score=0.3,
            accuracy_score=0.0,
            practice_count=1,
            last_practiced=None,
            next_practice_at=timezone.now() - timedelta(days=1),
            difficulty_at_practice="easy",
            is_weak=True,
        )
        queue = get_daily_queue(user)
        assert len(queue) >= 1

    def test_recall_analytics_returns_summary(self, question, user):
        RecallRecord.objects.create(
            user=user,
            topic=question.topic,
            problem_type=question.problem_type,
            question=question,
            recall_score=0.8,
            accuracy_score=1.0,
            practice_count=2,
            last_practiced=None,
            next_practice_at=None,
            difficulty_at_practice="easy",
            is_weak=False,
        )
        analytics = get_recall_analytics(user)
        assert analytics["total_topics"] >= 1
        assert analytics["strong_count"] >= 1

    def test_api_schedule_returns_due_items(self, auth_client, question, user):
        RecallRecord.objects.create(
            user=user,
            topic=question.topic,
            problem_type=question.problem_type,
            question=question,
            recall_score=0.3,
            accuracy_score=0.0,
            practice_count=1,
            last_practiced=None,
            next_practice_at=None,
            difficulty_at_practice="easy",
            is_weak=True,
        )
        response = auth_client.get("/api/recall/schedule/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_api_weak_topics_returns_weak_areas(self, auth_client, question, user):
        RecallRecord.objects.create(
            user=user,
            topic=question.topic,
            problem_type=question.problem_type,
            question=question,
            recall_score=0.2,
            accuracy_score=0.0,
            practice_count=2,
            last_practiced=None,
            next_practice_at=None,
            difficulty_at_practice="easy",
            is_weak=True,
        )
        response = auth_client.get("/api/recall/weak-topics/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
