from rest_framework import serializers
from backend.apps.questions.models import UploadedQuestion


class UploadQuestionSerializer(serializers.Serializer):
    image = serializers.ImageField()


class UploadedQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedQuestion
        fields = [
            "id",
            "user",
            "image",
            "extracted_text",
            "detected_topic",
            "detected_problem_type",
            "status",
            "solution",
            "ocr_confidence",
            "ocr_provider",
            "error_message",
            "question_candidates",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]


class UploadResultSerializer(serializers.Serializer):
    upload_id = serializers.IntegerField()
    status = serializers.CharField()
    text = serializers.CharField()
    questions = serializers.ListField(child=serializers.DictField())
    ocr_provider = serializers.CharField(required=False)
    ocr_confidence = serializers.FloatField(required=False, allow_null=True)


class UploadSolveSerializer(serializers.Serializer):
    upload_id = serializers.IntegerField()
    question_index = serializers.IntegerField(min_value=1)
