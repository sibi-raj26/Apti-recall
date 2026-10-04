from rest_framework import serializers
from .models import VoiceExplanation


class VoiceExplanationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceExplanation
        fields = ["id", "question", "attempt", "audio_file", "text_content", "language", "duration_seconds", "created_at"]
        read_only_fields = ["id", "created_at"]
