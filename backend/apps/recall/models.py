from django.db import models
from backend.apps.users.models import User
from backend.apps.topics.models import Topic, ProblemType
from backend.apps.questions.models import Question


class RecallRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recall_records")
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="recall_records")
    problem_type = models.ForeignKey(ProblemType, on_delete=models.CASCADE, null=True, blank=True, related_name="recall_records")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True, related_name="recall_records")
    recall_score = models.FloatField(default=0.0)
    accuracy_score = models.FloatField(default=0.0)
    practice_count = models.PositiveIntegerField(default=0)
    last_practiced = models.DateTimeField(null=True, blank=True)
    next_practice_at = models.DateTimeField(null=True, blank=True)
    difficulty_at_practice = models.CharField(max_length=10, blank=True)
    is_weak = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "topic", "problem_type", "question"]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Recall {self.user_id} - {self.topic_id}"
