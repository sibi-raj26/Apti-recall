import pytest
from backend.apps.solve.models import UserAttempt, VerificationRecord
from backend.apps.users.models import User
from backend.apps.topics.models import Topic, ProblemType
from backend.apps.questions.models import Question


@pytest.mark.django_db
def test_solve_app_import():
    from backend.apps.solve import apps
    assert apps.SolveConfig.name == "backend.apps.solve"


@pytest.mark.django_db
def test_user_attempt_creation():
    user = User.objects.create_user(email="attempt@example.com", username="attempter", password="pass123")
    topic = Topic.objects.create(name="Percentage", slug="percentage", order=1)
    pt = ProblemType.objects.create(topic=topic, name="percentage-basic")
    question = Question.objects.create(
        topic=topic,
        problem_type=pt,
        difficulty="easy",
        question_text="What is 10% of 200?",
        correct_answer="20",
        explanation_concept="Basic percentage",
        explanation_approach="Multiply",
        explanation_steps=[],
    )
    attempt = UserAttempt.objects.create(user=user, question=question, status="completed", is_correct=True, time_taken_seconds=10)
    assert attempt.status == "completed"
    assert attempt.is_correct is True


@pytest.mark.django_db
def test_verification_record_creation():
    user = User.objects.create_user(email="verify@example.com", username="verifier", password="pass123")
    topic = Topic.objects.create(name="HCF and LCM", slug="hcf-and-lcm", order=6)
    pt = ProblemType.objects.create(topic=topic, name="hcf-lcm")
    question = Question.objects.create(
        topic=topic,
        problem_type=pt,
        difficulty="medium",
        question_text="Find LCM of 12 and 18",
        correct_answer="36",
        explanation_concept="LCM",
        explanation_approach="Prime factorization",
        explanation_steps=[],
    )
    attempt = UserAttempt.objects.create(user=user, question=question)
    record = VerificationRecord.objects.create(attempt=attempt, method="algebraic", input_data={}, expected_result="36", actual_result="36", is_verified=True)
    assert record.is_verified is True
    assert record.method == "algebraic"
