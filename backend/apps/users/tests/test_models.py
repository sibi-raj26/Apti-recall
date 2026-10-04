import pytest
from backend.apps.users.models import User, UserProfile


@pytest.mark.django_db
def test_users_app_import():
    from backend.apps.users import apps
    assert apps.UsersConfig.name == "backend.apps.users"


@pytest.mark.django_db
def test_user_creation():
    user = User.objects.create_user(email="model@example.com", username="modeluser", password="modelpass")
    assert user.email == "model@example.com"
    assert user.check_password("modelpass")
    assert user.level == "beginner"


@pytest.mark.django_db
def test_user_profile_creation():
    user = User.objects.create_user(email="profile@example.com", username="profiler", password="pass123")
    profile = UserProfile.objects.create(user=user)
    assert profile is not None
    assert profile.overall_accuracy == 0.0
    assert profile.total_questions_attempted == 0
