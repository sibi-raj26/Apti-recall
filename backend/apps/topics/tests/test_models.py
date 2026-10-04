import pytest
from backend.apps.topics.models import Topic, Subtopic, ProblemType, Formula


@pytest.mark.django_db
def test_topics_app_import():
    from backend.apps.topics import apps
    assert apps.TopicsConfig.name == "backend.apps.topics"


@pytest.mark.django_db
def test_topic_creation(db):
    topic = Topic.objects.create(name="Profit and Loss", slug="profit-and-loss", order=2)
    assert topic.is_active is True
    assert topic.order == 2


@pytest.mark.django_db
def test_subtopic_creation(db):
    topic = Topic.objects.create(name="Time and Work", slug="time-and-work", order=3)
    subtopic = Subtopic.objects.create(topic=topic, name="Work Efficiency", order=1)
    assert subtopic.topic_id == topic.id


@pytest.mark.django_db
def test_problem_type_unique_together(db):
    topic = Topic.objects.create(name="Average", slug="average", order=4)
    ProblemType.objects.create(topic=topic, name="simple-average")
    from django.db import IntegrityError
    with pytest.raises(IntegrityError):
        ProblemType.objects.create(topic=topic, name="simple-average")


@pytest.mark.django_db
def test_formula_creation(db):
    topic = Topic.objects.create(name="Simple Interest", slug="simple-interest", order=5)
    pt = ProblemType.objects.create(topic=topic, name="si-basic")
    formula = Formula.objects.create(topic=topic, problem_type=pt, name="SI", formula_latex="P*r*t/100")
    assert formula.problem_type_id == pt.id
