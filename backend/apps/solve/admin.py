from django.contrib import admin
from .models import UserAttempt, VerificationRecord


@admin.register(UserAttempt)
class UserAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "question", "status", "is_correct", "hints_used", "time_taken_seconds", "created_at")
    list_filter = ("status", "is_correct", "question__topic", "question__difficulty")
    search_fields = ("user__email", "question__question_text", "user_answer")
    ordering = ("-created_at",)


@admin.register(VerificationRecord)
class VerificationRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "attempt", "method", "is_verified", "created_at")
    list_filter = ("method", "is_verified")
    search_fields = ("expected_result", "actual_result", "method")
    ordering = ("-created_at",)
