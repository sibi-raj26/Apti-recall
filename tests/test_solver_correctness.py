import pytest
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from backend.apps.users.models import User
from backend.apps.topics.models import Topic, ProblemType
from backend.apps.questions.models import Question
from backend.apps.solve.models import UserAttempt
from backend.apps.solve.services.verification_service import (
    PercentageOfStrategy,
    PercentageChangeStrategy,
    ProfitLossStrategy,
    AverageStrategy,
    normalize_answer,
    compare_normalized,
    VERIFICATION_STATUS_VERIFIED,
    VERIFICATION_STATUS_FAILED,
    VERIFICATION_STATUS_UNABLE,
)


class TestSolverCorrectness:
    def test_percentage_of_strategy_verifies_correct_answer(self):
        strategy = PercentageOfStrategy()
        result = strategy.verify("What is 20% of 150?", "30", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED
        assert result.confidence == 1.0

    def test_percentage_of_strategy_rejects_wrong_answer(self):
        strategy = PercentageOfStrategy()
        result = strategy.verify("What is 20% of 150?", "25", [])
        assert result.status == VERIFICATION_STATUS_FAILED

    def test_percentage_of_strategy_handles_decimals(self):
        strategy = PercentageOfStrategy()
        result = strategy.verify("What is 12.5% of 240?", "30", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_percentage_change_strategy_verifies_correct_answer(self):
        strategy = PercentageChangeStrategy()
        result = strategy.verify("from 100 to 120", "20", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_profit_loss_strategy_verifies_correct_answer(self):
        strategy = ProfitLossStrategy()
        result = strategy.verify("Cost price is 100, selling price is 120", "20", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_average_strategy_verifies_correct_answer(self):
        strategy = AverageStrategy()
        result = strategy.verify("average of 10 20 30", "20", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_normalize_answer_extracts_numeric_value(self):
        assert normalize_answer("30") == 30.0
        assert normalize_answer("30%") == 30.0
        assert normalize_answer("1/2") == 0.5
        assert normalize_answer("abc") is None

    def test_compare_normalized_with_tolerance(self):
        assert compare_normalized("30", "30.001", tolerance=1e-2) is True
        assert compare_normalized("30", "31", tolerance=1e-2) is False

    def test_api_solve_text_returns_valid_structure(self, db):
        user = User.objects.create_user(email="solver@example.com", username="solver", password="pass123")
        topic = Topic.objects.create(name="Percentage", slug="percentage", order=1)
        problem_type = ProblemType.objects.create(topic=topic, name="percentage-basic")
        question = Question.objects.create(
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

        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = client.post("/api/solve/text/", {"question_text": question.question_text}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert "question_text" in data
        assert "final_answer" in data
        assert "steps" in data
        assert "verification_status" in data

    def test_api_solve_history_returns_attempts(self, db):
        user = User.objects.create_user(email="history@example.com", username="historyuser", password="pass123")
        topic = Topic.objects.create(name="Percentage", slug="percentage", order=1)
        problem_type = ProblemType.objects.create(topic=topic, name="percentage-basic")
        question = Question.objects.create(
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
        UserAttempt.objects.create(
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

        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = client.get("/api/solve/history/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) >= 1
