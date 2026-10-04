import pytest
from backend.apps.questions.models import Question, SolutionStep, Shortcut, UploadedQuestion
from backend.apps.users.models import User
from backend.apps.topics.models import Topic, ProblemType


@pytest.mark.django_db
def test_questions_app_import():
    from backend.apps.questions import apps
    assert apps.QuestionsConfig.name == "backend.apps.questions"


@pytest.mark.django_db
def test_question_creation(db):
    user = User.objects.create_user(email="quser@example.com", username="quser", password="pass123")
    topic = Topic.objects.create(name="Profit and Loss", slug="profit-and-loss", order=2)
    pt = ProblemType.objects.create(topic=topic, name="profit-percent")
    question = Question.objects.create(
        topic=topic,
        problem_type=pt,
        difficulty="medium",
        question_text="A sells an article to B at 20% profit. B sells to C at 10% profit. Find overall profit %?",
        correct_answer="32%",
        explanation_concept="Successive profit percentages.",
        explanation_approach="Use successive percentage formula.",
        explanation_steps=[],
        created_by=user,
    )
    assert question.difficulty == "medium"
    assert question.created_by_id == user.id


@pytest.mark.django_db
def test_solution_step_unique_constraint():
    user = User.objects.create_user(email="stepuser@example.com", username="stepuser", password="pass123")
    topic = Topic.objects.create(name="Profit and Loss", slug="profit-and-loss", order=2)
    pt = ProblemType.objects.create(topic=topic, name="profit-percent")
    question = Question.objects.create(
        topic=topic,
        problem_type=pt,
        difficulty="medium",
        question_text="Test question for steps",
        correct_answer="30",
        explanation_concept="Test",
        explanation_approach="Test",
        explanation_steps=[],
        created_by=user,
    )
    SolutionStep.objects.create(question=question, step_number=1, title="Step 1", description="desc")
    from django.db import IntegrityError
    with pytest.raises(IntegrityError):
        SolutionStep.objects.create(question=question, step_number=1, title="Step 1 again", description="desc2")


@pytest.mark.django_db
def test_uploaded_question_status():
    user = User.objects.create_user(email="uploader@example.com", username="uploader", password="pass123")
    topic = Topic.objects.create(name="Average", slug="average", order=4)
    pt = ProblemType.objects.create(topic=topic, name="simple-average")
    upload = UploadedQuestion.objects.create(user=user, image="uploads/test.png", detected_topic=topic, detected_problem_type=pt)
    assert upload.status == "pending"
