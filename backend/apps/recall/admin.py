from django.contrib import admin
from .models import RecallRecord


@admin.register(RecallRecord)
class RecallRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "topic", "problem_type", "question", "recall_score", "accuracy_score", "practice_count", "is_weak", "next_practice_at")
    list_filter = ("topic", "is_weak", "next_practice_at")
    search_fields = ("user__email", "topic__name", "problem_type__name")
    ordering = ("-updated_at",)
