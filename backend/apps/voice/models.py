from django.db import models
from backend.apps.questions.models import Question
from backend.apps.solve.models import UserAttempt


class VoiceExplanation(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="voice_explanations")
    attempt = models.ForeignKey(UserAttempt, on_delete=models.CASCADE, null=True, blank=True, related_name="voice_explanations")
    audio_file = models.FileField(upload_to="audio/explanations/")
    text_content = models.TextField()
    language = models.CharField(max_length=10, default="en")
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Voice {self.pk} - Q{self.question_id}"
