from django.contrib.auth import authenticate
from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView

from .models import UserProfile
from .permissions import IsAdmin, IsOwner
from .serializers import ChangePasswordSerializer, LoginSerializer, RegisterSerializer, UserProfileSerializer, UserSerializer


class RegisterView(views.APIView):
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "success": True,
            "data": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response({
            "success": True,
            "data": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        })


class LogoutView(views.APIView):
    permission_classes = []

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({
                "success": False,
                "error": {"code": "VALIDATION_ERROR", "message": "Refresh token is required."}
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({
                "success": False,
                "error": {"code": "INVALID_TOKEN", "message": "Invalid or expired refresh token."}
            }, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": True, "data": {"message": "Logged out successfully."}})


class TokenRefreshView(BaseTokenRefreshView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        data = response.data
        return Response({
            "success": True,
            "data": data,
        })


class CurrentUserView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"success": True, "data": UserSerializer(request.user).data})


class ProfileView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response({"success": True, "data": serializer.data})

    def patch(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(instance=profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})


class ChangePasswordView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"success": True, "data": {"message": "Password changed successfully."}})
