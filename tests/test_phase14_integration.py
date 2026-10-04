import io
import math
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image as PILImage
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

from backend.apps.users.models import User, UserProfile
from backend.apps.topics.models import Topic, Subtopic, ProblemType, Formula
from backend.apps.questions.models import Question, SolutionStep, Shortcut, UploadedQuestion
from backend.apps.solve.models import UserAttempt, VerificationRecord
from backend.apps.recall.models import RecallRecord
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
    _verify_steps,
    _safe_eval_expression,
    VERIFICATION_STATUS_VERIFIED,
    VERIFICATION_STATUS_FAILED,
    VERIFICATION_STATUS_UNABLE,
)
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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="phase14@example.com",
        username="phase14user",
        password="phase14pass123",
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
        is_active=True,
        created_by=user,
    )


@pytest.fixture
def solution_step(db, question):
    return SolutionStep.objects.create(question=question, step_number=1, title="Calculate fraction", description="20/100 = 0.2")


@pytest.fixture
def shortcut(db, question):
    return Shortcut.objects.create(question=question, title="Quick method", description="Divide by 5 directly.")


# ---------------------------------------------------------------------------
# 1. End-to-End Auth Flow
# ---------------------------------------------------------------------------

class TestEndToEndAuthFlow:
    def test_register_login_refresh_profile_logout(self, api_client):
        # Register
        reg_resp = api_client.post("/api/auth/register/", {
            "email": "e2e_auth@example.com",
            "username": "e2e_auth_user",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
        }, format="json")
        assert reg_resp.status_code == status.HTTP_201_CREATED
        access = reg_resp.data["data"]["access"]
        refresh_token = reg_resp.data["data"]["refresh"]

        # Profile via access token (profile returns UserProfile data, not User data)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        profile_resp = client.get("/api/auth/profile/")
        assert profile_resp.status_code == status.HTTP_200_OK
        assert profile_resp.data["success"] is True

        # Refresh
        refresh_resp = api_client.post("/api/auth/refresh/", {"refresh": refresh_token}, format="json")
        assert refresh_resp.status_code == status.HTTP_200_OK
        assert "access" in refresh_resp.data["data"]

        # Logout
        logout_resp = client.post("/api/auth/logout/", {"refresh": refresh_token}, format="json")
        assert logout_resp.status_code == status.HTTP_200_OK

    def test_invalid_token_rejected(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.here")
        resp = api_client.get("/api/auth/profile/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cross_user_profile_isolation(self, api_client):
        user1 = User.objects.create_user(email="u1@example.com", username="u1", password="pass123")
        user2 = User.objects.create_user(email="u2@example.com", username="u2", password="pass123")
        refresh1 = RefreshToken.for_user(user1)
        client1 = APIClient()
        client1.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh1.access_token}")

        resp = client1.get("/api/auth/profile/")
        assert resp.status_code == status.HTTP_200_OK
        profile = UserProfile.objects.get(user=user1)
        assert profile.user_id == user1.id


# ---------------------------------------------------------------------------
# 2. End-to-End Learning Flow
# ---------------------------------------------------------------------------

class TestEndToEndLearningFlow:
    def test_complete_learning_chain(self, auth_client, topic, problem_type, subtopic, formula, question, solution_step, shortcut):
        # Topics list
        topics_resp = auth_client.get("/api/topics/")
        assert topics_resp.status_code == status.HTTP_200_OK
        assert topics_resp.data["success"] is True

        # Topic detail
        detail_resp = auth_client.get(f"/api/topics/{topic.id}/")
        assert detail_resp.status_code == status.HTTP_200_OK
        assert detail_resp.data["data"]["name"] == "Percentage"
        assert len(detail_resp.data["data"]["subtopics"]) >= 1
        assert len(detail_resp.data["data"]["problem_types"]) >= 1
        assert len(detail_resp.data["data"]["formulas"]) >= 1

        # Questions list
        questions_resp = auth_client.get("/api/questions/")
        assert questions_resp.status_code == status.HTTP_200_OK
        assert questions_resp.data["success"] is True

        # Question detail
        q_detail = auth_client.get(f"/api/questions/{question.id}/")
        assert q_detail.status_code == status.HTTP_200_OK
        assert q_detail.data["data"]["correct_answer"] == "30"

        # Solution
        sol_resp = auth_client.get(f"/api/questions/{question.id}/solution/")
        assert sol_resp.status_code == status.HTTP_200_OK
        assert len(sol_resp.data["data"]) >= 1

        # Shortcut
        sc_resp = auth_client.get(f"/api/questions/{question.id}/shortcut/")
        assert sc_resp.status_code == status.HTTP_200_OK
        assert len(sc_resp.data["data"]) >= 1


# ---------------------------------------------------------------------------
# 3. End-to-End Solve Flow
# ---------------------------------------------------------------------------

class TestEndToEndSolveFlow:
    def test_text_solve_creates_attempt_and_history(self, auth_client, question):
        solve_resp = auth_client.post("/api/solve/text/", {"question_text": question.question_text}, format="json")
        assert solve_resp.status_code == status.HTTP_200_OK
        assert solve_resp.data["success"] is True
        data = solve_resp.data["data"]
        assert "attempt_id" in data
        assert "verification_status" in data
        assert data["verification_status"] in {
            VERIFICATION_STATUS_VERIFIED,
            VERIFICATION_STATUS_FAILED,
            VERIFICATION_STATUS_UNABLE,
            "NOT_VERIFIED",
        }
        attempt_id = data["attempt_id"]
        assert UserAttempt.objects.filter(id=attempt_id, user=question.created_by).exists()

        # History
        history_resp = auth_client.get("/api/solve/history/")
        assert history_resp.status_code == status.HTTP_200_OK
        assert len(history_resp.data["data"]) >= 1

    def test_solve_unseen_question(self, auth_client):
        with patch("backend.apps.solve.views.SolveService") as mock_solver_cls:
            mock_solver = MagicMock()
            mock_solver.solve.return_value = {
                "question_text": "What is 15% of 200?",
                "topic": {"id": 1, "name": "Percentage"},
                "problem_type": {"id": 1, "name": "percentage-basic"},
                "concept": "Percentage concept.",
                "approach": "Multiply.",
                "steps": [],
                "final_answer": "30",
                "shortcut": "",
                "confidence": 0.9,
                "verification_status": VERIFICATION_STATUS_VERIFIED,
                "verification_details": {},
                "source": "ai_generated",
                "attempt_id": 999,
            }
            mock_solver_cls.return_value = mock_solver

            solve_resp = auth_client.post("/api/solve/text/", {"question_text": "What is 15% of 200?"}, format="json")
            assert solve_resp.status_code == status.HTTP_200_OK
            assert solve_resp.data["success"] is True

    def test_solve_rejects_empty_and_long_input(self, auth_client):
        resp_empty = auth_client.post("/api/solve/text/", {"question_text": ""}, format="json")
        assert resp_empty.status_code == status.HTTP_400_BAD_REQUEST

        resp_ws = auth_client.post("/api/solve/text/", {"question_text": "   "}, format="json")
        assert resp_ws.status_code == status.HTTP_400_BAD_REQUEST

        resp_long = auth_client.post("/api/solve/text/", {"question_text": "x" * 5001}, format="json")
        assert resp_long.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# 4. End-to-End Upload/OCR/Solve Flow
# ---------------------------------------------------------------------------

class TestEndToEndUploadSolveFlow:
    def test_complete_upload_solve_chain(self, auth_client, user, topic, problem_type):
        # Upload image
        buffer = io.BytesIO()
        image = PILImage.new("RGB", (100, 50), (255, 255, 255))
        image.save(buffer, format="PNG")
        buffer.seek(0)
        buffer.name = "test.png"

        mock_preprocessed = MagicMock(path="/tmp/test.png", width=100, height=50, format="PNG")
        mock_ocr = MagicMock(text="A train travels 120 km in 2 hours.", confidence=0.9, provider="tesseract", language="eng", status="success")

        with patch("backend.apps.upload.views.ImagePreprocessor") as mock_preprocessor_cls, \
             patch("backend.apps.upload.views.OCRService") as mock_ocr_cls:
            mock_preprocessor_cls.return_value = MagicMock(preprocess=MagicMock(return_value=mock_preprocessed))
            mock_ocr_cls.return_value = MagicMock(extract_text=MagicMock(return_value=mock_ocr))

            upload_resp = auth_client.post("/api/upload/image/", {"image": buffer}, format="multipart")
            assert upload_resp.status_code == status.HTTP_200_OK
            upload_id = upload_resp.data["data"]["upload_id"]
            assert UploadedQuestion.objects.filter(id=upload_id, user=user).exists()

            # Status
            status_resp = auth_client.get(f"/api/upload/{upload_id}/status/")
            assert status_resp.status_code == status.HTTP_200_OK

            # Result
            result_resp = auth_client.get(f"/api/upload/{upload_id}/result/")
            assert result_resp.status_code == status.HTTP_200_OK

        # Solve selected question
        with patch("backend.apps.upload.views.SolveService") as mock_solver_cls:
            mock_solver = MagicMock()
            mock_solver.solve.return_value = {
                "question_text": "A train travels 120 km in 2 hours. Find its average speed.",
                "topic": {"id": topic.id, "name": topic.name},
                "problem_type": {"id": problem_type.id, "name": problem_type.name},
                "concept": "Average speed = total distance / total time.",
                "approach": "Divide distance by time.",
                "steps": [],
                "final_answer": "60 km/h",
                "shortcut": "",
                "confidence": 0.9,
                "verification_status": VERIFICATION_STATUS_VERIFIED,
                "verification_details": {},
                "source": "ai_generated",
                "attempt_id": 998,
            }
            mock_solver_cls.return_value = mock_solver

            solve_resp = auth_client.post("/api/upload/solve/", {"upload_id": upload_id, "question_index": 1}, format="json")
            assert solve_resp.status_code == status.HTTP_200_OK
            assert solve_resp.data["data"]["final_answer"] == "60 km/h"

    def test_upload_ownership_enforced(self, auth_client, user):
        other_user = User.objects.create_user(email="other@example.com", username="other", password="pass123")
        upload = UploadedQuestion.objects.create(user=other_user, image="uploads/questions/other.png", status="ocr_completed")

        buffer = io.BytesIO()
        image = PILImage.new("RGB", (100, 50), (255, 255, 255))
        image.save(buffer, format="PNG")
        buffer.seek(0)
        buffer.name = "test.png"

        with patch("backend.apps.upload.views.ImagePreprocessor") as mock_preprocessor_cls, \
             patch("backend.apps.upload.views.OCRService") as mock_ocr_cls:
            mock_preprocessor_cls.return_value = MagicMock(preprocess=MagicMock(return_value=MagicMock(path="/tmp/test.png", width=100, height=50, format="PNG")))
            mock_ocr_cls.return_value = MagicMock(extract_text=MagicMock(return_value=MagicMock(text="text", confidence=0.9, provider="tesseract", language="eng", status="success")))

            resp = auth_client.post("/api/upload/solve/", {"upload_id": upload.id, "question_index": 1}, format="json")
            assert resp.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# 5. End-to-End Practice Flow
# ---------------------------------------------------------------------------

class TestEndToEndPracticeFlow:
    def test_practice_generate_returns_verified_question(self, auth_client, question):
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
                "verification_status": VERIFICATION_STATUS_VERIFIED,
                "verification_details": {},
                "source": "generated",
                "attempt": 1,
            }
            mock_practice_cls.return_value = mock_practice

            resp = auth_client.post("/api/practice/generate/", {"question_id": question.id}, format="json")
            assert resp.status_code == status.HTTP_200_OK
            assert resp.data["data"]["final_answer"] == "50"


# ---------------------------------------------------------------------------
# 6. End-to-End Recall Flow
# ---------------------------------------------------------------------------

class TestEndToEndRecallFlow:
    def test_recall_submit_updates_record(self, auth_client, question, user):
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

        submit_resp = auth_client.post("/api/recall/submit/", {"attempt_id": attempt.id}, format="json")
        assert submit_resp.status_code == status.HTTP_200_OK
        record.refresh_from_db()
        assert record.practice_count == 1
        assert record.last_practiced is not None

    def test_recall_schedule_returns_due_items(self, auth_client, question, user):
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
        resp = auth_client.get("/api/recall/schedule/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["success"] is True

    def test_recall_weak_topics_and_analytics(self, auth_client, question, user):
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
        weak_resp = auth_client.get("/api/recall/weak-topics/")
        assert weak_resp.status_code == status.HTTP_200_OK

        analytics_resp = auth_client.get("/api/recall/analytics/")
        assert analytics_resp.status_code == status.HTTP_200_OK
        assert analytics_resp.data["data"]["total_topics"] >= 1


# ---------------------------------------------------------------------------
# 7. Verification Status Cross-Cutting Tests
# ---------------------------------------------------------------------------

class TestVerificationStatusCrossCutting:
    def test_all_verification_statuses_accepted_by_solve_api(self, auth_client):
        for status_val in [VERIFICATION_STATUS_VERIFIED, VERIFICATION_STATUS_FAILED, VERIFICATION_STATUS_UNABLE]:
            with patch("backend.apps.solve.views.SolveService") as mock_solver_cls:
                mock_solver = MagicMock()
                mock_solver.solve.return_value = {
                    "question_text": "test",
                    "topic": {"id": 1, "name": "Percentage"},
                    "problem_type": {"id": 1, "name": "percentage-basic"},
                    "concept": "concept",
                    "approach": "approach",
                    "steps": [],
                    "final_answer": "30",
                    "shortcut": "",
                    "confidence": 0.9,
                    "verification_status": status_val,
                    "verification_details": {},
                    "source": "ai_generated",
                    "attempt_id": 1,
                }
                mock_solver_cls.return_value = mock_solver

                resp = auth_client.post("/api/solve/text/", {"question_text": "test question"}, format="json")
                assert resp.status_code == status.HTTP_200_OK
                assert resp.data["data"]["verification_status"] == status_val

    def test_verify_endpoint_returns_all_statuses(self, auth_client, user, question):
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
            solution_feedback={"source": "ai_generated", "verification_status": "PENDING"},
        )

        for status_val in [VERIFICATION_STATUS_VERIFIED, VERIFICATION_STATUS_FAILED, VERIFICATION_STATUS_UNABLE]:
            with patch("backend.apps.solve.views.VerificationService") as mock_verify_cls:
                mock_verify = MagicMock()
                mock_verify.verify.return_value = MagicMock(
                    status=status_val,
                    method="TEST_METHOD",
                    confidence=0.8,
                    details="test details",
                    checks=[],
                    expected="50",
                    actual="50",
                )
                mock_verify_cls.return_value = mock_verify

                resp = auth_client.post("/api/solve/verify/", {"attempt_id": attempt.id}, format="json")
                assert resp.status_code == status.HTTP_200_OK
                assert resp.data["data"]["status"] == status_val
                attempt.solution_feedback = {"source": "ai_generated", "verification_status": "PENDING"}
                attempt.save()


# ---------------------------------------------------------------------------
# 8. Error / Failure Handling
# ---------------------------------------------------------------------------

class TestErrorFailureHandling:
    def test_upload_rejects_oversized_image(self, auth_client):
        large_buffer = io.BytesIO(b"x" * (11 * 1024 * 1024))
        large_buffer.name = "large.png"
        resp = auth_client.post("/api/upload/image/", {"image": large_buffer}, format="multipart")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_rejects_invalid_file_type(self, auth_client):
        buffer = io.BytesIO(b"not an image")
        buffer.name = "test.txt"
        resp = auth_client.post("/api/upload/image/", {"image": buffer}, format="multipart")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_solve_returns_500_when_ai_raises(self, auth_client):
        with patch("backend.apps.solve.views.SolveService") as mock_solver_cls:
            mock_solver = MagicMock()
            mock_solver.solve.side_effect = Exception("AI unavailable")
            mock_solver_cls.return_value = mock_solver

            resp = auth_client.post("/api/solve/text/", {"question_text": "test"}, format="json")
            assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_upload_solve_rejects_invalid_question_index(self, auth_client, user):
        upload = UploadedQuestion.objects.create(
            user=user,
            image="uploads/questions/test.png",
            status="ocr_completed",
            question_candidates=[{"index": 1, "text": "question 1"}],
        )
        resp = auth_client.post("/api/upload/solve/", {"upload_id": upload.id, "question_index": 5}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthorized_routes_return_401(self, api_client):
        routes = [
            ("/api/topics/", "get"),
            ("/api/questions/", "get"),
            ("/api/solve/text/", "post"),
            ("/api/upload/image/", "post"),
            ("/api/recall/schedule/", "get"),
            ("/api/practice/generate/", "post"),
            ("/api/auth/me/", "get"),
            ("/api/auth/profile/", "get"),
        ]
        for route, method in routes:
            if method == "get":
                resp = api_client.get(route)
            else:
                resp = api_client.post(route, {}, format="json")
            assert resp.status_code == status.HTTP_401_UNAUTHORIZED, f"Expected 401 for {route}, got {resp.status_code}"


# ---------------------------------------------------------------------------
# 9. Mathematical Solver Correctness — All Strategies
# ---------------------------------------------------------------------------

class TestMathematicalSolverCorrectness:
    def test_percentage_of_strategy_verifies_correct(self):
        strategy = PercentageOfStrategy()
        result = strategy.verify("What is 20% of 150?", "30", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_percentage_of_strategy_rejects_wrong(self):
        strategy = PercentageOfStrategy()
        result = strategy.verify("What is 20% of 150?", "25", [])
        assert result.status == VERIFICATION_STATUS_FAILED

    def test_percentage_change_strategy_verifies_correct(self):
        strategy = PercentageChangeStrategy()
        result = strategy.verify("from 100 to 120", "20", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_profit_loss_strategy_verifies_correct(self):
        strategy = ProfitLossStrategy()
        result = strategy.verify("Cost price is 100, selling price is 120", "20", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_average_strategy_verifies_correct(self):
        strategy = AverageStrategy()
        result = strategy.verify("average of 10 20 30", "20", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_simple_interest_strategy_verifies_correct(self):
        strategy = SimpleInterestStrategy()
        result = strategy.verify("P=1000, R=5, T=2", "100", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_simple_interest_strategy_rejects_wrong(self):
        strategy = SimpleInterestStrategy()
        result = strategy.verify("P=1000, R=5, T=2", "200", [])
        assert result.status == VERIFICATION_STATUS_FAILED

    def test_compound_interest_strategy_verifies_correct(self):
        strategy = CompoundInterestStrategy()
        result = strategy.verify("P=1000, R=10, T=1", "100", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_time_work_strategy_verifies_correct(self):
        strategy = TimeWorkStrategy()
        result = strategy.verify("A can do work in 10 days, B in 20 days", "6.67", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_pipes_cisterns_strategy_verifies_correct(self):
        strategy = PipesCisternsStrategy()
        result = strategy.verify("Inlet fills in 10 hours, outlet empties in 20 hours", "20", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_time_speed_distance_strategy_verifies_correct(self):
        strategy = TimeSpeedDistanceStrategy()
        result = strategy.verify("Speed=60, Time=2", "120", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_train_strategy_verifies_correct(self):
        strategy = TrainStrategy()
        result = strategy.verify("Train 100 m at 60 km/h crosses pole.", "6", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_hcf_lcm_strategy_verifies_correct(self):
        strategy = HcfLcmStrategy()
        result = strategy.verify("HCF of 12 and 18.", "6", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_probability_strategy_verifies_correct(self):
        strategy = ProbabilityStrategy()
        result = strategy.verify("A die is rolled. P(even) = 3/6.", "0.5", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_permutation_strategy_verifies_correct(self):
        strategy = PermutationCombinationStrategy()
        result = strategy.verify("Arrange 3 letters.", "6", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_combination_strategy_verifies_correct(self):
        strategy = PermutationCombinationStrategy()
        result = strategy.verify("Choose 3 from 5 people.", "10", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_ratio_strategy_verifies_correct(self):
        strategy = RatioStrategy()
        result = strategy.verify("Divide 100 in ratio 2:3", "40", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_number_system_strategy_verifies_correct(self):
        strategy = NumberSystemStrategy()
        result = strategy.verify("Remainder of 10 divided by 3", "1", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_ages_strategy_verifies_with_steps(self):
        strategy = AgesStrategy()
        result = strategy.verify("Father is 30, son is 10", "20", [{"step": 1, "calculation": "30-10=20"}])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_algebraic_strategy_verifies_correct(self):
        strategy = AlgebraicStrategy()
        result = strategy.verify("Solve 2x + 4 = 10", "3", [])
        assert result.status == VERIFICATION_STATUS_VERIFIED

    def test_default_strategy_handles_unknown(self):
        strategy = DefaultStrategy()
        result = strategy.verify("unknown question type", "42", [])
        assert result.status in {VERIFICATION_STATUS_VERIFIED, VERIFICATION_STATUS_FAILED, VERIFICATION_STATUS_UNABLE}

    def test_normalize_answer_handles_various_formats(self):
        assert normalize_answer("30") == 30.0
        assert normalize_answer("30%") == 30.0
        assert normalize_answer("1/2") == 0.5
        assert normalize_answer("abc") is None
        assert normalize_answer("") is None
        assert normalize_answer("   ") is None

    def test_compare_normalized_tolerance(self):
        assert compare_normalized("30", "30.001", tolerance=1e-2) is True
        assert compare_normalized("30", "31", tolerance=1e-2) is False
        assert compare_normalized("30", "30.0001", tolerance=1e-3) is True

    def test_safe_eval_blocks_arbitrary_code(self):
        assert _safe_eval_expression("import os") is None
        assert _safe_eval_expression("__import__('os')") is None
        assert _safe_eval_expression("2+2") == 4.0

    def test_verify_steps_detects_arithmetic_error(self):
        bad_steps = [{"step": 1, "calculation": "2+2=5"}]
        ok, msg, failed = _verify_steps(bad_steps)
        assert ok is False
        assert len(failed) >= 1

    def test_api_verify_endpoint_creates_record(self, auth_client, user, question):
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
            solution_feedback={
                "question_text": "What is 20% of 250?",
                "topic": {"slug": "percentage", "name": "Percentage"},
                "problem_type": {"name": "Finding Percentage"},
                "final_answer": "50",
                "steps": [],
            },
        )
        resp = auth_client.post("/api/solve/verify/", {"attempt_id": attempt.id}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert VerificationRecord.objects.filter(attempt=attempt).exists()


# ---------------------------------------------------------------------------
# 10. Recall Algorithm Edge Cases
# ---------------------------------------------------------------------------

class TestRecallAlgorithmEdgeCases:
    def test_score_clamped_between_zero_and_one(self, question, user):
        extreme_attempt = UserAttempt.objects.create(
            user=user,
            question=question,
            status="completed",
            is_correct=False,
            hints_used=10,
            attempts_count=10,
            time_taken_seconds=9999,
            viewed_solution=True,
            viewed_shortcut=True,
        )
        score = compute_recall_score(extreme_attempt)
        assert 0.0 <= score <= 1.0

    def test_correct_answer_with_no_penalties_scores_well(self, question, user):
        attempt = UserAttempt.objects.create(
            user=user,
            question=question,
            status="completed",
            is_correct=True,
            hints_used=0,
            attempts_count=1,
            time_taken_seconds=5,
            viewed_solution=False,
            viewed_shortcut=False,
        )
        score = compute_recall_score(attempt)
        assert score >= 0.45  # moderate or strong

    def test_hint_penalty_reduces_score(self, question, user):
        no_hint = UserAttempt.objects.create(
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
        with_hints = UserAttempt.objects.create(
            user=user,
            question=question,
            status="completed",
            is_correct=True,
            hints_used=3,
            attempts_count=1,
            time_taken_seconds=15,
            viewed_solution=False,
            viewed_shortcut=False,
        )
        assert compute_recall_score(no_hint) > compute_recall_score(with_hints)

    def test_shortcut_penalty_reduces_score(self, question, user):
        no_shortcut = UserAttempt.objects.create(
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
        with_shortcut = UserAttempt.objects.create(
            user=user,
            question=question,
            status="completed",
            is_correct=True,
            hints_used=0,
            attempts_count=1,
            time_taken_seconds=15,
            viewed_solution=True,
            viewed_shortcut=True,
        )
        assert compute_recall_score(no_shortcut) > compute_recall_score(with_shortcut)

    def test_weakness_detection_accuracy_below_50_percent(self, question, user):
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
            recall_score=0.3,
            accuracy_score=0.0,
            practice_count=0,
            last_practiced=None,
            next_practice_at=None,
            difficulty_at_practice="easy",
            is_weak=False,
        )
        recent = list(UserAttempt.objects.filter(user=user, question=question, status="completed").order_by("-created_at")[:20])
        record.is_weak = detect_weakness(record, recent)
        record.save()
        assert record.is_weak is True

    def test_daily_queue_returns_due_items(self, question, user):
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
        queue = list(get_daily_queue(user))
        assert len(queue) >= 1

    def test_recall_analytics_counts(self, question, user):
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
        assert analytics["weak_count"] == 0
        assert analytics["moderate_count"] == 0
        assert analytics["average_recall_score"] >= 0.0

    def test_update_recall_ema_smoothing(self, question, user):
        record = RecallRecord.objects.create(
            user=user,
            topic=question.topic,
            problem_type=question.problem_type,
            question=question,
            recall_score=0.9,
            accuracy_score=1.0,
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
            is_correct=False,
            hints_used=0,
            attempts_count=1,
            time_taken_seconds=15,
            viewed_solution=False,
            viewed_shortcut=False,
        )
        updated = update_recall(user, attempt)
        assert updated.recall_score < 0.9  # EMA should pull score down
        assert updated.practice_count == 1


# ---------------------------------------------------------------------------
# 11. Cross-Platform Data Consistency
# ---------------------------------------------------------------------------

class TestCrossPlatformDataConsistency:
    def test_solve_response_fields_match_contract(self, auth_client, question):
        resp = auth_client.post("/api/solve/text/", {"question_text": question.question_text}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data["data"]
        required_fields = [
            "question_text", "topic", "problem_type", "concept",
            "approach", "steps", "final_answer", "shortcut",
            "confidence", "verification_status", "source", "attempt_id",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        # verification_details is optional (only present for AI-generated responses)
        if "verification_details" in data:
            assert isinstance(data["verification_details"], dict)

    def test_topic_detail_contains_required_nested_objects(self, auth_client, topic, subtopic, problem_type, formula):
        resp = auth_client.get(f"/api/topics/{topic.id}/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data["data"]
        assert "subtopics" in data
        assert "problem_types" in data
        assert "formulas" in data
        assert len(data["subtopics"]) >= 1
        assert len(data["problem_types"]) >= 1
        assert len(data["formulas"]) >= 1

    def test_question_detail_contains_solution_and_shortcuts(self, auth_client, question, solution_step, shortcut):
        resp = auth_client.get(f"/api/questions/{question.id}/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data["data"]
        assert "solution_steps" in data
        assert "shortcuts" in data
        assert len(data["solution_steps"]) >= 1
        assert len(data["shortcuts"]) >= 1

    def test_recall_response_contains_all_required_fields(self, auth_client, question, user):
        RecallRecord.objects.create(
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
        resp = auth_client.get("/api/recall/schedule/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data["data"]
        assert isinstance(data, list)

        analytics_resp = auth_client.get("/api/recall/analytics/")
        analytics = analytics_resp.data["data"]
        required = ["total_topics", "weak_count", "moderate_count", "strong_count", "average_recall_score"]
        for field in required:
            assert field in analytics, f"Missing analytics field: {field}"


# ---------------------------------------------------------------------------
# 12. Ownership / Security
# ---------------------------------------------------------------------------

class TestOwnershipSecurity:
    def test_users_cannot_access_others_attempts(self, auth_client, user, question):
        other = User.objects.create_user(email="other14@example.com", username="other14", password="pass123")
        attempt = UserAttempt.objects.create(
            user=other,
            question=question,
            status="completed",
            is_correct=True,
            hints_used=0,
            attempts_count=1,
            time_taken_seconds=15,
            viewed_solution=False,
            viewed_shortcut=False,
        )
        resp = auth_client.post("/api/solve/verify/", {"attempt_id": attempt.id}, format="json")
        assert resp.status_code in {status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN}

    def test_users_cannot_access_others_uploads(self, auth_client, user):
        other = User.objects.create_user(email="other14b@example.com", username="other14b", password="pass123")
        upload = UploadedQuestion.objects.create(user=other, image="uploads/questions/other.png", status="ocr_completed")
        resp = auth_client.post("/api/upload/solve/", {"upload_id": upload.id, "question_index": 1}, format="json")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
