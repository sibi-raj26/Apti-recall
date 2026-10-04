from django.contrib import admin
from .models import VoiceExplanation


@admin.register(VoiceExplanation)
class VoiceExplanationAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "attempt", "language", "duration_seconds", "created_at")
    list_filter = ("language",)
    search_fields = ("text_content", "question__question_text")
    ordering = ("-created_at",)
