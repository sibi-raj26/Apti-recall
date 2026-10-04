from django.contrib import admin
from .models import Question, SolutionStep, Shortcut, UploadedQuestion


class SolutionStepInline(admin.TabularInline):
    model = SolutionStep
    extra = 1
    fields = ("step_number", "title", "description", "latex")
    ordering = ("step_number",)


class ShortcutInline(admin.TabularInline):
    model = Shortcut
    extra = 1
    fields = ("title", "description", "formula", "example")
    ordering = ("title",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "topic", "problem_type", "difficulty", "is_active", "created_by", "created_at")
    list_filter = ("topic", "problem_type", "difficulty", "is_active")
    search_fields = ("question_text", "correct_answer", "tags", "topic__name")
    ordering = ("-created_at",)
    inlines = [SolutionStepInline, ShortcutInline]


@admin.register(SolutionStep)
class SolutionStepAdmin(admin.ModelAdmin):
    list_display = ("question", "step_number", "title")
    list_filter = ("question__topic",)
    search_fields = ("title", "description", "question__question_text")
    ordering = ("question", "step_number")


@admin.register(Shortcut)
class ShortcutAdmin(admin.ModelAdmin):
    list_display = ("question", "title")
    list_filter = ("question__topic",)
    search_fields = ("title", "description", "formula")
    ordering = ("question", "title")


@admin.register(UploadedQuestion)
class UploadedQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "detected_topic", "detected_problem_type", "created_at")
    list_filter = ("status", "detected_topic", "detected_problem_type")
    search_fields = ("extracted_text", "user__email")
    ordering = ("-created_at",)
