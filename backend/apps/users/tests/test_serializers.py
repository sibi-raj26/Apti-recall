import pytest
from rest_framework import serializers

from backend.apps.users.models import User, UserProfile
from backend.apps.users.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserSerializer,
)


@pytest.mark.django_db
class TestUserSerializer:
    def test_serializes_expected_fields(self):
        user = User.objects.create_user(email="serial@example.com", username="serialuser", password="pass123")
        serializer = UserSerializer(user)
        data = serializer.data
        assert "id" in data
        assert "email" in data
        assert "username" in data
        assert "password" not in data

    def test_password_excluded_from_output(self):
        user = User.objects.create_user(email="nopass@example.com", username="nopass", password="pass123")
        serializer = UserSerializer(user)
        assert "password" not in serializer.data
        assert "password_hash" not in str(serializer.data)

    def test_readonly_fields_are_readonly(self):
        user = User.objects.create_user(email="readonly@example.com", username="readonly", password="pass123")
        serializer = UserSerializer(user)
        assert "id" in serializer.fields
        assert serializer.fields["id"].read_only is True


@pytest.mark.django_db
class TestUserProfileSerializer:
    def test_serializes_expected_fields(self):
        user = User.objects.create_user(email="prof@example.com", username="profiler", password="pass123")
        profile = UserProfile.objects.create(user=user)
        serializer = UserProfileSerializer(profile)
        data = serializer.data
        assert "id" in data
        assert "preferred_language" in data
        assert data["preferred_language"] == "en"

    def test_profile_does_not_expose_user_password(self):
        user = User.objects.create_user(email="safe@example.com", username="safe", password="pass123")
        profile = UserProfile.objects.create(user=user)
        serializer = UserProfileSerializer(profile)
        assert "password" not in serializer.data


@pytest.mark.django_db
class TestRegisterSerializer:
    def test_valid_data_creates_user(self):
        payload = {
            "email": "reg@example.com",
            "username": "reguser",
            "password": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        serializer = RegisterSerializer(data=payload)
        assert serializer.is_valid(raise_exception=False) or serializer.is_valid()
        user = serializer.save()
        assert user.email == payload["email"]
        assert user.username == payload["username"]
        assert user.check_password(payload["password"])

    def test_duplicate_email_raises_validation_error(self):
        User.objects.create_user(email="dup@example.com", username="existing", password="pass123")
        payload = {
            "email": "dup@example.com",
            "username": "newuser",
            "password": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        serializer = RegisterSerializer(data=payload)
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_password_mismatch_raises_validation_error(self):
        payload = {
            "email": "mismatch@example.com",
            "username": "mismatch",
            "password": "SecurePass123!",
            "password2": "DifferentPass!",
        }
        serializer = RegisterSerializer(data=payload)
        assert not serializer.is_valid()
        assert "password2" in serializer.errors

    def test_weak_password_raises_validation_error(self):
        payload = {
            "email": "weak@example.com",
            "username": "weak",
            "password": "123",
            "password2": "123",
        }
        serializer = RegisterSerializer(data=payload)
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_password_hashed_and_not_stored_plaintext(self):
        payload = {
            "email": "nopw@example.com",
            "username": "nopw",
            "password": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        serializer = RegisterSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        assert user.check_password("SecurePass123!")
        assert user.password != "SecurePass123!"
        assert "pbkdf2" in user.password

    def test_creates_user_profile(self):
        payload = {
            "email": "profile@example.com",
            "username": "profuser",
            "password": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        serializer = RegisterSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        assert hasattr(user, "profile")
        assert user.profile is not None
        assert user.profile.overall_accuracy == 0.0


@pytest.mark.django_db
class TestLoginSerializer:
    def test_valid_credentials_returns_user(self):
        user = User.objects.create_user(email="login@example.com", username="loginuser", password="mypassword")
        payload = {"email": "login@example.com", "password": "mypassword"}
        serializer = LoginSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["user"] == user

    def test_invalid_password_raises_error(self):
        User.objects.create_user(email="login2@example.com", username="login2", password="mypassword")
        payload = {"email": "login2@example.com", "password": "wrongpass"}
        serializer = LoginSerializer(data=payload)
        assert not serializer.is_valid()

    def test_nonexistent_email_raises_error(self):
        payload = {"email": "noone@example.com", "password": "anypass"}
        serializer = LoginSerializer(data=payload)
        assert not serializer.is_valid()

    def test_password_not_exposed_in_user(self):
        user = User.objects.create_user(email="safe@example.com", username="safe", password="mypassword")
        payload = {"email": "safe@example.com", "password": "mypassword"}
        serializer = LoginSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        validated_user = serializer.validated_data["user"]
        assert validated_user.password != "mypassword"
        assert "pbkdf2" in validated_user.password


@pytest.mark.django_db
class TestChangePasswordSerializer:
    def test_valid_data(self):
        user = User.objects.create_user(email="changepw@example.com", username="changepw", password="oldpass123")
        payload = {
            "current_password": "oldpass123",
            "new_password": "NewPass123!",
            "new_password2": "NewPass123!",
        }
        serializer = ChangePasswordSerializer(data=payload, context={"request": type("req", (), {"user": user})()})
        serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["new_password"] == "NewPass123!"

    def test_wrong_current_password(self):
        user = User.objects.create_user(email="wrongcurr@example.com", username="wrongcurr", password="oldpass123")
        payload = {
            "current_password": "wrongpass",
            "new_password": "NewPass123!",
            "new_password2": "NewPass123!",
        }
        serializer = ChangePasswordSerializer(data=payload, context={"request": type("req", (), {"user": user})()})
        assert not serializer.is_valid()
        assert "current_password" in serializer.errors

    def test_new_password_mismatch(self):
        user = User.objects.create_user(email="newmismatch@example.com", username="newmismatch", password="oldpass123")
        payload = {
            "current_password": "oldpass123",
            "new_password": "NewPass123!",
            "new_password2": "DifferentPass!",
        }
        serializer = ChangePasswordSerializer(data=payload, context={"request": type("req", (), {"user": user})()})
        assert not serializer.is_valid()
        assert "new_password2" in serializer.errors

    def test_weak_new_password(self):
        user = User.objects.create_user(email="weaknew@example.com", username="weaknew", password="oldpass123")
        payload = {
            "current_password": "oldpass123",
            "new_password": "123",
            "new_password2": "123",
        }
        serializer = ChangePasswordSerializer(data=payload, context={"request": type("req", (), {"user": user})()})
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
