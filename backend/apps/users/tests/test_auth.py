import pytest
from rest_framework.test import APIClient
from rest_framework import status

from backend.apps.users.models import User, UserProfile


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="authuser@example.com", username="authuser", password="authpass123")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


class TestRegistration:
    def test_valid_registration(self, api_client):
        payload = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        response = api_client.post("/api/auth/register/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.data["data"]
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["email"] == payload["email"]
        assert User.objects.filter(email=payload["email"]).exists()

    def test_duplicate_email(self, api_client, user):
        payload = {
            "email": user.email,
            "username": "another",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        response = api_client.post("/api/auth/register/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_username(self, api_client, user):
        payload = {
            "email": "another@example.com",
            "username": user.username,
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        response = api_client.post("/api/auth/register/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_mismatch(self, api_client):
        payload = {
            "email": "mismatch@example.com",
            "username": "mismatch",
            "password": "StrongPass123!",
            "password2": "DifferentPass123!",
        }
        response = api_client.post("/api/auth/register/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_weak_password(self, api_client):
        payload = {
            "email": "weak@example.com",
            "username": "weak",
            "password": "123",
            "password2": "123",
        }
        response = api_client.post("/api/auth/register/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_fields(self, api_client):
        response = api_client.post("/api/auth/register/", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLogin:
    def test_valid_login(self, api_client, user):
        payload = {"email": user.email, "password": "authpass123"}
        response = api_client.post("/api/auth/login/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["email"] == user.email

    def test_invalid_password(self, api_client, user):
        payload = {"email": user.email, "password": "wrongpass"}
        response = api_client.post("/api/auth/login/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_nonexistent_email(self, api_client):
        payload = {"email": "nouser@example.com", "password": "pass123"}
        response = api_client.post("/api/auth/login/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_fields(self, api_client):
        response = api_client.post("/api/auth/login/", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCurrentUser:
    def test_get_current_user(self, auth_client, user):
        response = auth_client.get("/api/auth/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["email"] == user.email

    def test_unauthenticated_current_user(self, api_client):
        response = api_client.get("/api/auth/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestProfile:
    def test_get_profile(self, auth_client, user):
        response = auth_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["preferred_language"] == "en"

    def test_patch_profile(self, auth_client, user):
        response = auth_client.patch("/api/auth/profile/", {"preferred_language": "fr"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["preferred_language"] == "fr"

    def test_unauthenticated_profile(self, api_client):
        response = api_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestChangePassword:
    def test_valid_change(self, auth_client, user):
        payload = {
            "current_password": "authpass123",
            "new_password": "NewStrongPass123!",
            "new_password2": "NewStrongPass123!",
        }
        response = auth_client.post("/api/auth/change-password/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("NewStrongPass123!")

    def test_wrong_current_password(self, auth_client):
        payload = {
            "current_password": "wrongpass",
            "new_password": "NewStrongPass123!",
            "new_password2": "NewStrongPass123!",
        }
        response = auth_client.post("/api/auth/change-password/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_mismatch(self, auth_client):
        payload = {
            "current_password": "authpass123",
            "new_password": "NewStrongPass123!",
            "new_password2": "DifferentPass123!",
        }
        response = auth_client.post("/api/auth/change-password/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLogout:
    def test_valid_logout(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = api_client.post("/api/auth/logout/", {"refresh": refresh_token}, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_logout_missing_refresh(self, auth_client):
        response = auth_client.post("/api/auth/logout/", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_invalid_refresh(self, auth_client):
        response = auth_client.post("/api/auth/logout/", {"refresh": "invalidtoken"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestTokenRefresh:
    def test_valid_refresh(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        response = api_client.post("/api/auth/refresh/", {"refresh": str(refresh)}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data["data"]

    def test_invalid_refresh(self, api_client):
        response = api_client.post("/api/auth/refresh/", {"refresh": "invalidtoken"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPermissions:
    def test_cross_user_profile_access(self, api_client, user):
        other = User.objects.create_user(email="other@example.com", username="other", password="otherpass")
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(other)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        response = api_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["preferred_language"] == "en"


class TestRegistrationSecurity:
    def test_password_not_in_response(self, api_client):
        payload = {
            "email": "secure@example.com",
            "username": "secureuser",
            "password": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        response = api_client.post("/api/auth/register/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        response_str = str(response.content)
        assert "SecurePass123!" not in response_str

    def test_password_hash_not_in_response(self, api_client):
        payload = {
            "email": "nohash@example.com",
            "username": "nohash",
            "password": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        response = api_client.post("/api/auth/register/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email="nohash@example.com")
        assert user.password != "SecurePass123!"
        assert "pbkdf2" in user.password
        response_str = str(response.content)
        assert "pbkdf2" not in response_str

    def test_registration_returns_tokens(self, api_client):
        payload = {
            "email": "tokens@example.com",
            "username": "tokenuser",
            "password": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        response = api_client.post("/api/auth/register/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.data["data"]
        assert "access" in data
        assert "refresh" in data
        assert len(data["access"]) > 0
        assert len(data["refresh"]) > 0

    def test_duplicate_email_case_insensitive(self, api_client, user):
        payload = {
            "email": user.email.upper(),
            "username": "caseuser",
            "password": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        response = api_client.post("/api/auth/register/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_email_format(self, api_client):
        payload = {
            "email": "notanemail",
            "username": "bademail",
            "password": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        response = api_client.post("/api/auth/register/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLoginSecurity:
    def test_password_not_in_login_response(self, api_client, user):
        payload = {"email": user.email, "password": "authpass123"}
        response = api_client.post("/api/auth/login/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        response_str = str(response.content)
        assert "authpass123" not in response_str

    def test_login_no_password_hash_in_response(self, api_client, user):
        payload = {"email": user.email, "password": "authpass123"}
        response = api_client.post("/api/auth/login/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        response_str = str(response.content)
        assert "pbkdf2" not in response_str

    def test_login_returns_user_fields_only(self, api_client, user):
        payload = {"email": user.email, "password": "authpass123"}
        response = api_client.post("/api/auth/login/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        user_data = data["user"]
        assert "id" in user_data
        assert "email" in user_data
        assert "username" in user_data
        assert "password" not in user_data
        assert "password_hash" not in str(user_data)


class TestProtectedEndpoints:
    def test_me_no_token_returns_401(self, api_client):
        response = api_client.get("/api/auth/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_no_token_returns_401(self, api_client):
        response = api_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_password_no_token_returns_401(self, api_client):
        response = api_client.post("/api/auth/change-password/", {
            "current_password": "pass",
            "new_password": "NewPass123!",
            "new_password2": "NewPass123!",
        }, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_access_token_returns_401(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.here")
        response = api_client.get("/api/auth/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_valid_access_token_allows_access(self, auth_client, user):
        response = auth_client.get("/api/auth/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["email"] == user.email

    def test_refresh_no_token_returns_400(self, api_client):
        response = api_client.post("/api/auth/refresh/", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestTokenRefresh:
    def test_refresh_returns_new_access_token(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        response = api_client.post("/api/auth/refresh/", {"refresh": str(refresh)}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert "access" in data
        new_access = data["access"]
        assert new_access != str(refresh.access_token)

    def test_blacklisted_refresh_rejected(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)
        refresh.blacklist()
        response = api_client.post("/api/auth/refresh/", {"refresh": refresh_token}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_malformed_refresh_token(self, api_client):
        response = api_client.post("/api/auth/refresh/", {"refresh": "not-a-valid-token"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogout:
    def test_blacklisted_refresh_rejected_after_logout(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = api_client.post("/api/auth/logout/", {"refresh": refresh_token}, format="json")
        assert response.status_code == status.HTTP_200_OK
        response2 = api_client.post("/api/auth/refresh/", {"refresh": refresh_token}, format="json")
        assert response2.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_token_still_valid_after_logout(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        api_client.post("/api/auth/logout/", {"refresh": refresh_token}, format="json")
        response = api_client.get("/api/auth/me/")
        assert response.status_code == status.HTTP_200_OK

    def test_logout_without_auth_returns_400(self, api_client):
        response = api_client.post("/api/auth/logout/", {"refresh": "sometoken"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestChangePassword:
    def test_unauthenticated_change_password_returns_401(self, api_client):
        payload = {
            "current_password": "authpass123",
            "new_password": "NewStrongPass123!",
            "new_password2": "NewStrongPass123!",
        }
        response = api_client.post("/api/auth/change-password/", payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_old_password_fails_after_change(self, auth_client, user):
        payload = {
            "current_password": "authpass123",
            "new_password": "BrandNewPass123!",
            "new_password2": "BrandNewPass123!",
        }
        response = auth_client.post("/api/auth/change-password/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        from django.contrib.auth import authenticate
        assert authenticate(request=None, email=user.email, password="authpass123") is None
        user.refresh_from_db()
        assert user.check_password("BrandNewPass123!")


class TestJWTSettings:
    def test_access_token_lifetime_configured(self):
        from django.conf import settings
        from datetime import timedelta
        assert "ACCESS_TOKEN_LIFETIME" in settings.SIMPLE_JWT
        lifetime = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        assert isinstance(lifetime, timedelta)

    def test_refresh_token_lifetime_configured(self):
        from django.conf import settings
        from datetime import timedelta
        assert "REFRESH_TOKEN_LIFETIME" in settings.SIMPLE_JWT
        lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
        assert isinstance(lifetime, timedelta)

    def test_auth_header_type_bearer(self):
        from django.conf import settings
        assert "Bearer" in settings.SIMPLE_JWT["AUTH_HEADER_TYPES"]

    def test_token_blacklist_app_installed(self):
        from django.conf import settings
        assert "rest_framework_simplejwt.token_blacklist" in settings.INSTALLED_APPS
