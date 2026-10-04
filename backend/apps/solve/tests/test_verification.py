import math
import pytest
from unittest.mock import MagicMock, patch
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from backend.apps.solve.models import UserAttempt, VerificationRecord
from backend.apps.solve.services.verification_service import (
    VerificationService,
    PercentageOfStrategy,
    PercentageChangeStrategy,
    ProfitLossStrategy,
    AverageStrategy,
    SimpleInterestStrategy,
    CompoundInterestStrategy,
    TimeWorkStrategy,
    PipesCisternsStrategy,
    TimeSpeedDistanceStrategy,
    TrainStrategy,
    HcfLcmStrategy,
    ProbabilityStrategy,
    PermutationCombinationStrategy,
    RatioStrategy,
    NumberSystemStrategy,
    AgesStrategy,
    AlgebraicStrategy,
    DefaultStrategy,
    normalize_answer,
    compare_normalized,
    _safe_eval_expression,
    _verify_steps,
    VERIFICATION_STATUS_VERIFIED,
    VERIFICATION_STATUS_FAILED,
    VERIFICATION_STATUS_UNABLE,
)
from backend.apps.users.models import User


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="verify@example.com", username="verifier", password="pass123")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def attempt(db, user):
    return UserAttempt.objects.create(user=user, status="completed", solution_feedback={})


class TestNormalizeAnswer:
    def test_integer(self):
        assert normalize_answer("25") == 25.0

    def test_float(self):
        assert normalize_answer("25.5") == 25.5

    def test_percentage(self):
        assert normalize_answer("25%") == 25.0

    def test_fraction(self):
        assert normalize_answer("1/2") == 0.5

    def test_currency(self):
        assert normalize_answer("₹210") == 210.0

    def test_commas(self):
        assert normalize_answer("1,000") == 1000.0

    def test_with_text(self):
        assert normalize_answer("12 seconds") == 12.0

    def test_none_for_empty(self):
        assert normalize_answer("") is None

    def test_none_for_garbage(self):
        assert normalize_answer("unknown") is None


class TestCompareNormalized:
    def test_exact_match(self):
        assert compare_normalized("25", "25") is True

    def test_tolerance(self):
        assert compare_normalized("25.0001", "25") is True

    def test_mismatch(self):
        assert compare_normalized("30", "25") is False

    def test_none_input(self):
        assert compare_normalized(None, "25") is None
        assert compare_normalized("25", None) is None


class TestSafeEvalExpression:
    def test_simple_addition(self):
        assert _safe_eval_expression("2 + 2") == 4.0

    def test_multiplication(self):
        assert _safe_eval_expression("3 * 4") == 12.0

    def test_division(self):
        assert _safe_eval_expression("10 / 4") == 2.5

    def test_complex_expression(self):
        assert _safe_eval_expression("250 * 20 / 100") == 50.0

    def test_invalid_expression(self):
        assert _safe_eval_expression("import os") is None

    def test_eval_not_used(self):
        assert _safe_eval_expression("__import__('os').system('id')") is None


class TestVerifySteps:
    def test_valid_steps(self):
        steps = [
            {"step": 1, "calculation": "250 - 200 = 50"},
            {"step": 2, "calculation": "50 / 200 * 100 = 25"},
        ]
        ok, details, failed = _verify_steps(steps)
        assert ok is True

    def test_invalid_step(self):
        steps = [
            {"step": 1, "calculation": "250 - 200 = 99"},
        ]
        ok, details, failed = _verify_steps(steps)
        assert ok is False

    def test_empty_steps(self):
        ok, details, failed = _verify_steps([])
        assert ok is True


class TestPercentageOfStrategy:
    def test_correct_answer(self):
        strategy = PercentageOfStrategy()
        result = strategy.verify("What is 20% of 250?", "50", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_incorrect_answer(self):
        strategy = PercentageOfStrategy()
        result = strategy.verify("What is 20% of 250?", "60", [])
        assert result.status == VERIFICATION_STATUS_FAILED

    def test_cannot_handle_other_topic(self):
        strategy = PercentageOfStrategy()
        assert strategy.can_handle("average", "", "What is 20% of 250?") is False

    def test_cannot_handle_non_percentage_question(self):
        strategy = PercentageOfStrategy()
        assert strategy.can_handle("percentage", "", "What is 2 + 2?") is False


class TestPercentageChangeStrategy:
    def test_increase_correct(self):
        strategy = PercentageChangeStrategy()
        result = strategy.verify("A number is increased from 200 to 250.", "25%", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_increase_incorrect(self):
        strategy = PercentageChangeStrategy()
        result = strategy.verify("A number is increased from 200 to 250.", "30%", [])
        assert result.status == VERIFICATION_STATUS_FAILED


class TestProfitLossStrategy:
    def test_profit_correct(self):
        strategy = ProfitLossStrategy()
        result = strategy.verify("A shopkeeper buys for 400 and sells for 500. What is his profit percent?", "25%", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_loss_correct(self):
        strategy = ProfitLossStrategy()
        result = strategy.verify("A man buys for 300 and sells for 270. What is his loss percent?", "10%", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_profit_incorrect(self):
        strategy = ProfitLossStrategy()
        result = strategy.verify("A shopkeeper buys for 400 and sells for 500.", "30%", [])
        assert result.status == VERIFICATION_STATUS_FAILED


class TestAverageStrategy:
    def test_average_correct(self):
        strategy = AverageStrategy()
        result = strategy.verify("The average of 60, 70, 80, and 90.", "75", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_average_incorrect(self):
        strategy = AverageStrategy()
        result = strategy.verify("The average of 60, 70, 80, and 90.", "80", [])
        assert result.status == VERIFICATION_STATUS_FAILED


class TestSimpleInterestStrategy:
    def test_si_correct(self):
        strategy = SimpleInterestStrategy()
        result = strategy.verify("Find SI on 2000 at 5% for 4 years.", "400", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_si_incorrect(self):
        strategy = SimpleInterestStrategy()
        result = strategy.verify("Find SI on 2000 at 5% for 4 years.", "500", [])
        assert result.status == VERIFICATION_STATUS_FAILED


class TestCompoundInterestStrategy:
    def test_ci_correct(self):
        strategy = CompoundInterestStrategy()
        result = strategy.verify("CI on 1000 for 2 years at 10%.", "210", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_ci_incorrect(self):
        strategy = CompoundInterestStrategy()
        result = strategy.verify("CI on 1000 for 2 years at 10%.", "200", [])
        assert result.status == VERIFICATION_STATUS_FAILED


class TestTimeWorkStrategy:
    def test_combined_work_correct(self):
        strategy = TimeWorkStrategy()
        result = strategy.verify("A in 12 days, B in 15 days. Together?", "6.67", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_combined_work_incorrect(self):
        strategy = TimeWorkStrategy()
        result = strategy.verify("A in 12 days, B in 15 days. Together?", "10", [])
        assert result.status == VERIFICATION_STATUS_FAILED


class TestPipesCisternsStrategy:
    def test_net_rate_correct(self):
        strategy = PipesCisternsStrategy()
        result = strategy.verify("Fill in 20 min, empty in 30 min. Both open?", "60", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_net_rate_incorrect(self):
        strategy = PipesCisternsStrategy()
        result = strategy.verify("Fill in 20 min, empty in 30 min. Both open?", "50", [])
        assert result.status == VERIFICATION_STATUS_FAILED


class TestTimeSpeedDistanceStrategy:
    def test_distance_correct(self):
        strategy = TimeSpeedDistanceStrategy()
        result = strategy.verify("Speed 60 km/h for 2 hours. Distance?", "120", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_distance_incorrect(self):
        strategy = TimeSpeedDistanceStrategy()
        result = strategy.verify("Speed 60 km/h for 2 hours. Distance?", "150", [])
        assert result.status == VERIFICATION_STATUS_FAILED


class TestTrainStrategy:
    def test_train_crossing_correct(self):
        strategy = TrainStrategy()
        result = strategy.verify("Train 100 m at 60 km/h crosses pole.", "6", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_train_crossing_incorrect(self):
        strategy = TrainStrategy()
        result = strategy.verify("Train 100 m at 60 km/h crosses pole.", "10", [])
        assert result.status == VERIFICATION_STATUS_FAILED


class TestHcfLcmStrategy:
    def test_hcf_correct(self):
        strategy = HcfLcmStrategy()
        result = strategy.verify("HCF of 12, 18, 24.", "6", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_lcm_correct(self):
        strategy = HcfLcmStrategy()
        result = strategy.verify("LCM of 12 and 18.", "36", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_incorrect(self):
        strategy = HcfLcmStrategy()
        result = strategy.verify("HCF of 12, 18, 24.", "12", [])
        assert result.status == VERIFICATION_STATUS_FAILED


class TestProbabilityStrategy:
    def test_simple_probability_correct(self):
        strategy = ProbabilityStrategy()
        result = strategy.verify("A die is rolled. P(even) = 3/6.", "0.5", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_insufficient_structure(self):
        strategy = ProbabilityStrategy()
        result = strategy.verify("What is the probability?", "1/2", [])
        assert result.status == VERIFICATION_STATUS_UNABLE


class TestPermutationCombinationStrategy:
    def test_permutation_correct(self):
        strategy = PermutationCombinationStrategy()
        result = strategy.verify("Arrange 3 letters.", "6", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_combination_correct(self):
        strategy = PermutationCombinationStrategy()
        result = strategy.verify("Choose 3 from 5 people.", "10", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_incorrect(self):
        strategy = PermutationCombinationStrategy()
        result = strategy.verify("Arrange 3 letters.", "5", [])
        assert result.status == VERIFICATION_STATUS_FAILED


class TestRatioStrategy:
    def test_ratio_division_correct(self):
        strategy = RatioStrategy()
        result = strategy.verify("Divide 6300 in ratio 2:3:4. B's share?", "2100", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_unsupported_ratio(self):
        strategy = RatioStrategy()
        result = strategy.verify("A:B = 2:3, B:C = 4:5. Find A:C.", "8:15", [])
        assert result.status == VERIFICATION_STATUS_UNABLE


class TestNumberSystemStrategy:
    def test_remainder_correct(self):
        strategy = NumberSystemStrategy()
        result = strategy.verify("Remainder when 120 divided by 7.", "1", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_unsupported(self):
        strategy = NumberSystemStrategy()
        result = strategy.verify("Sum of first 50 natural numbers.", "1275", [])
        assert result.status == VERIFICATION_STATUS_UNABLE


class TestAlgebraicStrategy:
    def test_correct_linear_equation(self):
        strategy = AlgebraicStrategy()
        result = strategy.verify("Solve x + 5 = 12", "x = 7", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_incorrect_answer(self):
        strategy = AlgebraicStrategy()
        result = strategy.verify("Solve x + 5 = 12", "x = 8", [])
        assert result.status == VERIFICATION_STATUS_FAILED

    def test_multiplication_equation(self):
        strategy = AlgebraicStrategy()
        result = strategy.verify("Solve 2x = 10", "x = 5", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_linear_equation_with_constant(self):
        strategy = AlgebraicStrategy()
        result = strategy.verify("Solve 3x + 2 = 11", "x = 3", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_equivalent_answer_format_numeric(self):
        strategy = AlgebraicStrategy()
        result = strategy.verify("Solve x + 5 = 12", "7", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_division_equation(self):
        strategy = AlgebraicStrategy()
        result = strategy.verify("Solve x / 2 = 5", "x = 10", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_parentheses_equation(self):
        strategy = AlgebraicStrategy()
        result = strategy.verify("Solve 2(x + 3) = 14", "x = 4", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_unsupported_ambiguous_input(self):
        strategy = AlgebraicStrategy()
        result = strategy.verify("What is x + y?", "42", [])
        assert result.status == VERIFICATION_STATUS_UNABLE

    def test_malicious_input_rejected(self):
        strategy = AlgebraicStrategy()
        result = strategy.verify("Solve __import__('os').system('id')", "42", [])
        assert result.status == VERIFICATION_STATUS_UNABLE

    def test_no_equation_in_question(self):
        strategy = AlgebraicStrategy()
        result = strategy.verify("What is 2 + 2?", "4", [])
        assert result.status == VERIFICATION_STATUS_UNABLE


class TestDefaultStrategy:
    def test_consistent_steps_verified(self):
        strategy = DefaultStrategy()
        steps = [{"step": 1, "calculation": "2 + 2 = 4"}]
        result = strategy.verify("2 + 2 = ?", "4", steps)
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_inconsistent_steps_failed(self):
        strategy = DefaultStrategy()
        steps = [{"step": 1, "calculation": "2 + 2 = 5"}]
        result = strategy.verify("2 + 2 = ?", "5", steps)
        assert result.status == VERIFICATION_STATUS_FAILED

    def test_no_steps_unable(self):
        strategy = DefaultStrategy()
        result = strategy.verify("Unknown question?", "42", [])
        assert result.status == VERIFICATION_STATUS_UNABLE


class TestVerificationServiceIntegration:
    def test_verify_creates_record(self, db, attempt, user):
        solve_output = {
            "question_text": "What is 20% of 250?",
            "topic": {"slug": "percentage", "name": "Percentage"},
            "problem_type": {"name": "Finding Percentage"},
            "final_answer": "50",
            "steps": [],
        }
        service = VerificationService()
        result = service.verify(attempt, solve_output)
        assert result.status in (VERIFICATION_STATUS_VERIFIED, VERIFICATION_STATUS_FAILED, VERIFICATION_STATUS_UNABLE)
        assert VerificationRecord.objects.filter(attempt=attempt).exists()

    def test_verify_updates_attempt_feedback(self, db, attempt, user):
        solve_output = {
            "question_text": "What is 20% of 250?",
            "topic": {"slug": "percentage", "name": "Percentage"},
            "problem_type": {"name": "Finding Percentage"},
            "final_answer": "50",
            "steps": [],
        }
        service = VerificationService()
        result = service.verify(attempt, solve_output)
        assert VerificationRecord.objects.filter(attempt=attempt).exists()
        record = VerificationRecord.objects.filter(attempt=attempt).order_by("-created_at").first()
        assert record.is_verified == (result.status == VERIFICATION_STATUS_VERIFIED)

    def test_verify_no_strategy_unable(self, db, attempt, user):
        solve_output = {
            "question_text": "Some completely unknown question xyz.",
            "topic": {"slug": "data-interpretation", "name": "Data Interpretation"},
            "problem_type": {"name": "Table Analysis"},
            "final_answer": "42",
            "steps": [],
        }
        service = VerificationService()
        result = service.verify(attempt, solve_output)
        assert result.status == VERIFICATION_STATUS_UNABLE


class TestVerifyAnswerAPI:
    def test_verify_requires_auth(self, api_client, attempt):
        response = api_client.post("/api/solve/verify/", {"attempt_id": attempt.id}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_success(self, auth_client, attempt, user):
        attempt.solution_feedback = {
            "question_text": "What is 20% of 250?",
            "topic": {"slug": "percentage", "name": "Percentage"},
            "problem_type": {"name": "Finding Percentage"},
            "final_answer": "50",
            "steps": [],
        }
        attempt.save()
        response = auth_client.post("/api/solve/verify/", {"attempt_id": attempt.id}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["status"] in (VERIFICATION_STATUS_VERIFIED, VERIFICATION_STATUS_FAILED, VERIFICATION_STATUS_UNABLE)

    def test_verify_not_found(self, auth_client):
        response = auth_client.post("/api/solve/verify/", {"attempt_id": 99999}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_verify_other_user_attempt(self, auth_client, attempt):
        other = User.objects.create_user(email="other@example.com", username="other", password="pass123")
        attempt.user = other
        attempt.save()
        response = auth_client.post("/api/solve/verify/", {"attempt_id": attempt.id}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_verify_invalid_attempt_id(self, auth_client):
        response = auth_client.post("/api/solve/verify/", {"attempt_id": 0}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_incorrect_answer_returns_failed(self, auth_client, user):
        attempt = UserAttempt.objects.create(
            user=user,
            status="completed",
            solution_feedback={
                "question_text": "What is 20% of 250?",
                "topic": {"slug": "percentage", "name": "Percentage"},
                "problem_type": {"name": "Finding Percentage"},
                "final_answer": "60",
                "steps": [],
            },
        )
        response = auth_client.post("/api/solve/verify/", {"attempt_id": attempt.id}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["status"] == VERIFICATION_STATUS_FAILED

    def test_verify_unable_question(self, auth_client, user):
        attempt = UserAttempt.objects.create(
            user=user,
            status="completed",
            solution_feedback={
                "question_text": "Explain the concept of gravity.",
                "topic": {"slug": "data-interpretation", "name": "Data Interpretation"},
                "problem_type": {"name": "Table Analysis"},
                "final_answer": "42",
                "steps": [],
            },
        )
        response = auth_client.post("/api/solve/verify/", {"attempt_id": attempt.id}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["status"] == VERIFICATION_STATUS_UNABLE


class TestSecurity:
    def test_no_eval_in_verification(self):
        assert _safe_eval_expression("__import__('os').system('id')") is None

    def test_verify_does_not_expose_internal_errors(self, auth_client, user):
        attempt = UserAttempt.objects.create(user=user, status="completed", solution_feedback={"broken": "value"})
        response = auth_client.post("/api/solve/verify/", {"attempt_id": attempt.id}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "traceback" not in str(response.data).lower()
