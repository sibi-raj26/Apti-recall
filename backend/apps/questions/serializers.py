from rest_framework import serializers
from .models import Question, SolutionStep, Shortcut, UploadedQuestion


class SolutionStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolutionStep
        fields = ["id", "question", "step_number", "title", "description", "latex"]
        read_only_fields = ["id"]


class ShortcutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shortcut
        fields = ["id", "question", "title", "description", "formula", "example"]
        read_only_fields = ["id"]


class QuestionListSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    problem_type_name = serializers.CharField(source="problem_type.name", read_only=True)
    subtopic_name = serializers.CharField(source="subtopic.name", read_only=True)

    class Meta:
        model = Question
        fields = [
            "id", "topic", "topic_name", "problem_type", "problem_type_name",
            "subtopic", "subtopic_name", "difficulty", "question_text",
            "correct_answer", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class QuestionDetailSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    problem_type_name = serializers.CharField(source="problem_type.name", read_only=True)
    subtopic_name = serializers.CharField(source="subtopic.name", read_only=True)
    solution_steps = SolutionStepSerializer(many=True, read_only=True)
    shortcuts = ShortcutSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id", "topic", "topic_name", "problem_type", "problem_type_name",
            "subtopic", "subtopic_name", "difficulty", "question_text",
            "question_latex", "correct_answer", "correct_answer_latex",
            "explanation_concept", "explanation_approach",
            "hints", "tags", "is_active", "created_at", "updated_at",
            "solution_steps", "shortcuts",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UploadedQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedQuestion
        fields = ["id", "user", "image", "extracted_text", "detected_topic", "detected_problem_type", "status", "solution", "created_at"]
        read_only_fields = ["id", "created_at"]
