import pytest
from unittest.mock import MagicMock

from backend.apps.solve.services.solver_service import SolveService
from backend.apps.solve.services.verification_service import (
    VERIFICATION_STATUS_VERIFIED,
    VERIFICATION_STATUS_FAILED,
    VERIFICATION_STATUS_UNABLE,
)
from backend.apps.solve.models import UserAttempt
from backend.apps.topics.models import Topic, ProblemType, Subtopic
from backend.apps.questions.models import Question, SolutionStep, Shortcut
from backend.apps.users.models import User


class TestSolveServiceExistingQuestion:
    def test_exact_match_returns_existing(self, db):
        user = User.objects.create_user(email="solver@example.com", username="solver", password="pass123")
        topic = Topic.objects.create(name="Percentage", slug="percentage", order=1)
        pt = ProblemType.objects.create(topic=topic, name="percentage-basic")
        question = Question.objects.create(
            topic=topic,
            problem_type=pt,
            difficulty="easy",
            question_text="What is 20% of 250?",
            correct_answer="50",
            explanation_concept="Basic percentage.",
            explanation_approach="Multiply.",
            explanation_steps=[],
            is_active=True,
        )
        SolutionStep.objects.create(question=question, step_number=1, title="Step 1", description="desc")
        Shortcut.objects.create(question=question, title="Shortcut", description="short", formula="", example="")

        service = SolveService()
        result = service.solve(user, "What is 20% of 250?")
        assert result["source"] == "existing"
        assert result["final_answer"] == "50"
        assert result["verification_status"] == "NOT_VERIFIED"
        assert len(result["steps"]) == 1
        assert result["attempt_id"] is not None
        assert UserAttempt.objects.filter(id=result["attempt_id"]).exists()

    def test_no_match_calls_ai(self, db):
        user = User.objects.create_user(email="solver2@example.com", username="solver2", password="pass123")
        mock_provider = MagicMock()
        mock_provider.structured_call.return_value = {
            "question_understanding": "Test question",
            "topic": "percentage",
            "problem_type": "percentage-basic",
            "concept": "Test concept",
            "approach": "Test approach",
            "steps": [{"step": 1, "title": "S1", "calculation": "1+1", "explanation": "add"}],
            "final_answer": "42",
            "shortcut": "",
            "confidence": 0.9,
        }
        service = SolveService(llm_client=mock_provider)
        result = service.solve(user, "What is 7 + 35?")
        assert result["source"] == "ai_generated"
        assert result["final_answer"] == "42"
        assert result["verification_status"] in (VERIFICATION_STATUS_VERIFIED, VERIFICATION_STATUS_FAILED, VERIFICATION_STATUS_UNABLE)
        assert mock_provider.structured_call.called


class TestSolveServiceValidation:
    def test_empty_question_raises(self, db):
        user = User.objects.create_user(email="v@example.com", username="v", password="pass123")
        service = SolveService()
        with pytest.raises(ValueError, match="Question text is required"):
            service.solve(user, "")

    def test_whitespace_only_question_raises(self, db):
        user = User.objects.create_user(email="v2@example.com", username="v2", password="pass123")
        service = SolveService()
        with pytest.raises(ValueError, match="Question text is required"):
            service.solve(user, "   ")

    def test_too_long_question_raises(self, db):
        user = User.objects.create_user(email="v3@example.com", username="v3", password="pass123")
        service = SolveService()
        with pytest.raises(ValueError, match="exceeds maximum length"):
            service.solve(user, "a" * 5001)


class TestSolveServiceAISubprocess:
    def test_ai_unavailable_raises(self, db):
        user = User.objects.create_user(email="v4@example.com", username="v4", password="pass123")
        mock_provider = MagicMock()
        mock_provider.structured_call.side_effect = RuntimeError("Provider down")
        service = SolveService(llm_client=mock_provider)
        with pytest.raises(RuntimeError, match="Provider down"):
            service.solve(user, "A unique unseen question xyz?")

    def test_ai_timeout_raises(self, db):
        import requests
        user = User.objects.create_user(email="v5@example.com", username="v5", password="pass123")
        mock_provider = MagicMock()
        mock_provider.structured_call.side_effect = requests.exceptions.Timeout("Timed out")
        service = SolveService(llm_client=mock_provider)
        with pytest.raises(requests.exceptions.Timeout):
            service.solve(user, "Another unique question abc?")


class TestSolveServiceValidationOutput:
    def test_missing_required_field_raises(self, db):
        user = User.objects.create_user(email="v6@example.com", username="v6", password="pass123")
        mock_provider = MagicMock()
        mock_provider.structured_call.return_value = {"final_answer": "42"}
        service = SolveService(llm_client=mock_provider)
        with pytest.raises(ValueError, match="missing required field"):
            service.solve(user, "Unique question missing fields?")

    def test_empty_steps_raises(self, db):
        user = User.objects.create_user(email="v7@example.com", username="v7", password="pass123")
        mock_provider = MagicMock()
        mock_provider.structured_call.return_value = {
            "question_understanding": "q", "topic": "", "problem_type": "",
            "concept": "c", "approach": "a", "steps": [], "final_answer": "42",
        }
        service = SolveService(llm_client=mock_provider)
        with pytest.raises(ValueError, match="non-empty list"):
            service.solve(user, "Unique question empty steps?")

    def test_missing_step_field_raises(self, db):
        user = User.objects.create_user(email="v8@example.com", username="v8", password="pass123")
        mock_provider = MagicMock()
        mock_provider.structured_call.return_value = {
            "question_understanding": "q", "topic": "", "problem_type": "",
            "concept": "c", "approach": "a",
            "steps": [{"step": 1}],
            "final_answer": "42",
        }
        service = SolveService(llm_client=mock_provider)
        with pytest.raises(ValueError, match="missing field"):
            service.solve(user, "Unique question missing step field?")

    def test_missing_confidence_defaults_to_zero(self, db):
        user = User.objects.create_user(email="v9@example.com", username="v9", password="pass123")
        mock_provider = MagicMock()
        mock_provider.structured_call.return_value = {
            "question_understanding": "q", "topic": "", "problem_type": "",
            "concept": "c", "approach": "a",
            "steps": [{"step": 1, "title": "t", "calculation": "c", "explanation": "e"}],
            "final_answer": "42",
        }
        service = SolveService(llm_client=mock_provider)
        result = service.solve(user, "Unique question no confidence?")
        assert result["confidence"] == 0.0

    def test_invalid_confidence_clamped(self, db):
        user = User.objects.create_user(email="v10@example.com", username="v10", password="pass123")
        mock_provider = MagicMock()
        mock_provider.structured_call.return_value = {
            "question_understanding": "q", "topic": "", "problem_type": "",
            "concept": "c", "approach": "a",
            "steps": [{"step": 1, "title": "t", "calculation": "c", "explanation": "e"}],
            "final_answer": "42",
            "confidence": 1.5,
        }
        service = SolveService(llm_client=mock_provider)
        result = service.solve(user, "Unique question bad confidence?")
        assert result["confidence"] == 1.0


class TestSolveServiceTopicMatching:
    def test_topic_matched(self, db):
        user = User.objects.create_user(email="tm@example.com", username="tm", password="pass123")
        topic = Topic.objects.create(name="Percentage", slug="percentage", order=1)
        mock_provider = MagicMock()
        mock_provider.structured_call.return_value = {
            "question_understanding": "q", "topic": "percentage", "problem_type": "",
            "concept": "c", "approach": "a",
            "steps": [{"step": 1, "title": "t", "calculation": "c", "explanation": "e"}],
            "final_answer": "42",
        }
        service = SolveService(llm_client=mock_provider)
        result = service.solve(user, "Unique topic match question")
        assert result["topic"]["id"] == topic.id
        assert result["topic"]["name"] == topic.name

    def test_topic_not_matched_returns_none(self, db):
        user = User.objects.create_user(email="tnm@example.com", username="tnm", password="pass123")
        mock_provider = MagicMock()
        mock_provider.structured_call.return_value = {
            "question_understanding": "q", "topic": "nonexistent-topic", "problem_type": "",
            "concept": "c", "approach": "a",
            "steps": [{"step": 1, "title": "t", "calculation": "c", "explanation": "e"}],
            "final_answer": "42",
        }
        service = SolveService(llm_client=mock_provider)
        result = service.solve(user, "Unique no topic match question")
        assert result["topic"] is None

    def test_problem_type_matched(self, db):
        user = User.objects.create_user(email="ptm@example.com", username="ptm", password="pass123")
        topic = Topic.objects.create(name="Percentage", slug="percentage", order=1)
        pt = ProblemType.objects.create(topic=topic, name="percentage-increase")
        mock_provider = MagicMock()
        mock_provider.structured_call.return_value = {
            "question_understanding": "q", "topic": "percentage", "problem_type": "percentage-increase",
            "concept": "c", "approach": "a",
            "steps": [{"step": 1, "title": "t", "calculation": "c", "explanation": "e"}],
            "final_answer": "42",
        }
        service = SolveService(llm_client=mock_provider)
        result = service.solve(user, "Unique pt match question")
        assert result["problem_type"]["id"] == pt.id
        assert result["problem_type"]["name"] == pt.name
