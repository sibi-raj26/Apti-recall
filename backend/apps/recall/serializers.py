from rest_framework import serializers
from .models import RecallRecord


class RecallRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecallRecord
        fields = [
            "id", "user", "topic", "problem_type", "question",
            "recall_score", "accuracy_score", "practice_count",
            "last_practiced", "next_practice_at", "difficulty_at_practice",
            "is_weak", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
