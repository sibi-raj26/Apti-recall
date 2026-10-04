from django.db import models
from backend.apps.users.models import User
from backend.apps.topics.models import Topic, Subtopic, ProblemType


class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="questions")
    problem_type = models.ForeignKey(ProblemType, on_delete=models.CASCADE, related_name="questions")
    subtopic = models.ForeignKey(Subtopic, on_delete=models.CASCADE, null=True, blank=True, related_name="questions")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    question_text = models.TextField()
    question_latex = models.TextField(blank=True)
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.TextField()
    correct_answer_latex = models.TextField(blank=True)
    explanation_concept = models.TextField()
    explanation_steps = models.JSONField(default=list)
    explanation_approach = models.TextField()
    explanation_shortcut = models.TextField(blank=True)
    hints = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.question_text[:80]


class SolutionStep(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="solution_steps")
    step_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    latex = models.TextField(blank=True)

    class Meta:
        unique_together = ["question", "step_number"]
        ordering = ["step_number"]

    def __str__(self):
        return f"{self.question_id} - Step {self.step_number}"


class Shortcut(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="shortcuts")
    title = models.CharField(max_length=200)
    description = models.TextField()
    formula = models.TextField(blank=True)
    example = models.TextField(blank=True)

    class Meta:
        ordering = ["question", "title"]

    def __str__(self):
        return self.title


class UploadedQuestion(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("ocr_completed", "OCR Completed"),
        ("failed", "Failed"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploaded_questions")
    image = models.ImageField(upload_to="uploads/questions/")
    extracted_text = models.TextField(blank=True)
    detected_topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    detected_problem_type = models.ForeignKey(ProblemType, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    solution = models.JSONField(default=dict, blank=True)
    ocr_confidence = models.FloatField(null=True, blank=True)
    ocr_provider = models.CharField(max_length=50, blank=True)
    error_message = models.TextField(blank=True)
    question_candidates = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"UploadedQuestion {self.pk} - {self.status}"
