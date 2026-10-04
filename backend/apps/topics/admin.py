from django.contrib import admin
from .models import Topic, Subtopic, ProblemType, Formula


class SubtopicInline(admin.TabularInline):
    model = Subtopic
    extra = 1
    fields = ("name", "description", "order")
    ordering = ("order", "name")


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description")
    ordering = ("order", "name")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [SubtopicInline]


@admin.register(Subtopic)
class SubtopicAdmin(admin.ModelAdmin):
    list_display = ("topic", "name", "order")
    list_filter = ("topic",)
    search_fields = ("name", "description", "topic__name")
    ordering = ("topic__name", "order")


@admin.register(ProblemType)
class ProblemTypeAdmin(admin.ModelAdmin):
    list_display = ("topic", "subtopic", "name", "is_active")
    list_filter = ("topic", "is_active")
    search_fields = ("name", "description", "topic__name", "keywords")
    ordering = ("topic__name", "name")


@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    list_display = ("topic", "problem_type", "name", "formula_latex")
    list_filter = ("topic", "problem_type")
    search_fields = ("name", "formula_latex", "description", "variables")
    ordering = ("topic__name", "name")
