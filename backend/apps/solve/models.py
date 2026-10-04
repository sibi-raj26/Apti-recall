from django.db import models
from backend.apps.users.models import User
from backend.apps.questions.models import Question, UploadedQuestion


class UserAttempt(models.Model):
    ATTEMPT_STATUS = [
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("abandoned", "Abandoned"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attempts")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="attempts", null=True, blank=True)
    uploaded_question = models.ForeignKey(UploadedQuestion, on_delete=models.CASCADE, null=True, blank=True, related_name="attempts")
    status = models.CharField(max_length=20, choices=ATTEMPT_STATUS, default="in_progress")
    user_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    hints_used = models.PositiveIntegerField(default=0)
    attempts_count = models.PositiveIntegerField(default=1)
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)
    viewed_solution = models.BooleanField(default=False)
    viewed_shortcut = models.BooleanField(default=False)
    viewed_concept = models.BooleanField(default=False)
    solution_feedback = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Attempt {self.pk} - User {self.user_id}"


class VerificationRecord(models.Model):
    attempt = models.ForeignKey(UserAttempt, on_delete=models.CASCADE, related_name="verification_records")
    method = models.CharField(max_length=50)
    input_data = models.JSONField()
    expected_result = models.TextField()
    actual_result = models.TextField()
    is_verified = models.BooleanField()
    verification_details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Verification {self.method} - Attempt {self.attempt_id}"
