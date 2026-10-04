from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import User, UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "username", "phone", "avatar", "level", "streak_days", "last_active", "date_joined"]
        read_only_fields = ["id", "date_joined", "last_active"]


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["id", "total_questions_attempted", "total_questions_solved", "overall_accuracy", "preferred_language"]
        read_only_fields = ["id"]


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email is already registered.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username is already taken.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Password fields did not match."})
        try:
            validate_password(attrs["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages})
        return attrs

    def create(self, validated_data):
        data = {**validated_data}
        data.pop("password2")
        password = data.pop("password")
        user = User(**data)
        user.set_password(password)
        user.save()
        UserProfile.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        from django.contrib.auth import authenticate
        user = authenticate(request=None, email=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        attrs["user"] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password2 = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError({"new_password2": "Password fields did not match."})
        try:
            validate_password(attrs["new_password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": exc.messages})
        return attrs
