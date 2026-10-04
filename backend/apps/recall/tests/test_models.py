import pytest
from backend.apps.recall.models import RecallRecord
from backend.apps.users.models import User
from backend.apps.topics.models import Topic, ProblemType
from backend.apps.questions.models import Question


@pytest.mark.django_db
def test_recall_app_import():
    from backend.apps.recall import apps
    assert apps.RecallConfig.name == "backend.apps.recall"


@pytest.mark.django_db
def test_recall_record_creation():
    user = User.objects.create_user(email="recall@example.com", username="recaller", password="pass123")
    topic = Topic.objects.create(name="Probability", slug="probability", order=14)
    pt = ProblemType.objects.create(topic=topic, name="simple-probability")
    question = Question.objects.create(
        topic=topic,
        problem_type=pt,
        difficulty="easy",
        question_text="Probability of heads?",
        correct_answer="1/2",
        explanation_concept="Basic probability",
        explanation_approach="Favorable/Total",
        explanation_steps=[],
    )
    record = RecallRecord.objects.create(user=user, topic=topic, problem_type=pt, question=question, recall_score=0.9, accuracy_score=1.0)
    assert record.is_weak is False
    assert record.recall_score == 0.9


@pytest.mark.django_db
def test_recall_unique_constraint():
    user = User.objects.create_user(email="recall2@example.com", username="recaller2", password="pass123")
    topic = Topic.objects.create(name="Permutation and Combination", slug="permutation-and-combination", order=15)
    pt = ProblemType.objects.create(topic=topic, name="permutation")
    question = Question.objects.create(
        topic=topic,
        problem_type=pt,
        difficulty="medium",
        question_text="Permutation test",
        correct_answer="12",
        explanation_concept="Permutation",
        explanation_approach="nPr",
        explanation_steps=[],
    )
    RecallRecord.objects.create(user=user, topic=topic, problem_type=pt, question=question)
    from django.db import IntegrityError
    with pytest.raises(IntegrityError):
        RecallRecord.objects.create(user=user, topic=topic, problem_type=pt, question=question)
