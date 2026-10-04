import pytest
from backend.apps.voice.models import VoiceExplanation
from backend.apps.users.models import User
from backend.apps.topics.models import Topic, ProblemType
from backend.apps.questions.models import Question
from backend.apps.solve.models import UserAttempt


@pytest.mark.django_db
def test_voice_app_import():
    from backend.apps.voice import apps
    assert apps.VoiceConfig.name == "backend.apps.voice"


@pytest.mark.django_db
def test_voice_explanation_creation():
    user = User.objects.create_user(email="voice@example.com", username="voicer", password="pass123")
    topic = Topic.objects.create(name="Data Interpretation", slug="data-interpretation", order=16)
    pt = ProblemType.objects.create(topic=topic, name="table")
    question = Question.objects.create(
        topic=topic,
        problem_type=pt,
        difficulty="medium",
        question_text="Table DI question",
        correct_answer="100",
        explanation_concept="Table reading",
        explanation_approach="Analyze rows and columns",
        explanation_steps=[],
    )
    attempt = UserAttempt.objects.create(user=user, question=question)
    voice = VoiceExplanation.objects.create(question=question, attempt=attempt, audio_file="audio/test.mp3", text_content="Hello", language="en")
    assert voice.language == "en"
    assert voice.attempt_id == attempt.id
