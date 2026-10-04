from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    level = models.CharField(max_length=20, default="beginner")
    streak_days = models.PositiveIntegerField(default=0)
    last_active = models.DateField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ["-created_at"]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    total_questions_attempted = models.PositiveIntegerField(default=0)
    total_questions_solved = models.PositiveIntegerField(default=0)
    overall_accuracy = models.FloatField(default=0.0)
    preferred_language = models.CharField(max_length=10, default="en")

    class Meta:
        ordering = ["-user__created_at"]

