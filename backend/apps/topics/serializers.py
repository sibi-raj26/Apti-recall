from rest_framework import serializers
from .models import Topic, Subtopic, ProblemType, Formula


class SubtopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtopic
        fields = ["id", "topic", "name", "description", "order"]
        read_only_fields = ["id"]


class ProblemTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemType
        fields = ["id", "topic", "subtopic", "name", "description", "keywords", "solving_strategy", "is_active"]
        read_only_fields = ["id"]


class FormulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Formula
        fields = ["id", "topic", "problem_type", "name", "formula_latex", "description", "variables", "example_usage"]
        read_only_fields = ["id"]


class TopicListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "name", "slug", "description", "icon", "order", "is_active"]
        read_only_fields = ["id"]


class TopicDetailSerializer(serializers.ModelSerializer):
    subtopics = SubtopicSerializer(many=True, read_only=True)
    problem_types = ProblemTypeSerializer(many=True, read_only=True)
    formulas = FormulaSerializer(many=True, read_only=True)

    class Meta:
        model = Topic
        fields = [
            "id", "name", "slug", "description", "icon", "order", "is_active",
            "created_at", "subtopics", "problem_types", "formulas",
        ]
        read_only_fields = ["id", "created_at"]
