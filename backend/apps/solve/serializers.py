from rest_framework import serializers
from .models import UserAttempt, VerificationRecord


class UserAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAttempt
        fields = [
            "id", "user", "question", "uploaded_question", "status",
            "user_answer", "is_correct", "hints_used", "attempts_count",
            "time_taken_seconds", "viewed_solution", "viewed_shortcut",
            "viewed_concept", "solution_feedback", "created_at", "completed_at",
        ]
        read_only_fields = ["id", "created_at"]


class VerificationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationRecord
        fields = ["id", "attempt", "method", "input_data", "expected_result", "actual_result", "is_verified", "verification_details", "created_at"]
        read_only_fields = ["id", "created_at"]


class SolveStepSerializer(serializers.Serializer):
    step = serializers.IntegerField()
    title = serializers.CharField()
    calculation = serializers.CharField()
    explanation = serializers.CharField()


class SolveRequestSerializer(serializers.Serializer):
    question_text = serializers.CharField(
        max_length=5000,
        trim_whitespace=False,
        help_text="The aptitude question text to solve.",
    )

    def validate_question_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Question text cannot be empty.")
        return value.strip()


class SolveResponseSerializer(serializers.Serializer):
    question_text = serializers.CharField()
    topic = serializers.DictField(allow_null=True)
    problem_type = serializers.DictField(allow_null=True)
    concept = serializers.CharField()
    approach = serializers.CharField()
    steps = SolveStepSerializer(many=True)
    final_answer = serializers.CharField()
    shortcut = serializers.CharField()
    confidence = serializers.FloatField()
    verification_status = serializers.CharField()
    verification_details = serializers.DictField(required=False)
    source = serializers.CharField()
    attempt_id = serializers.IntegerField()


class VerifyRequestSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField()

    def validate_attempt_id(self, value):
        if value <= 0:
            raise serializers.ValidationError("attempt_id must be a positive integer.")
        return value


class VerifyResponseSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField()
    status = serializers.CharField()
    method = serializers.CharField()
    confidence = serializers.FloatField()
    details = serializers.CharField()
    checks = serializers.ListField(child=serializers.CharField())
    expected = serializers.CharField(allow_null=True, required=False)
    actual = serializers.CharField(allow_null=True, required=False)
