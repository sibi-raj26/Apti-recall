from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("refresh/", views.TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", views.CurrentUserView.as_view(), name="current-user"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),
]
