from django.db import models


class Topic(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Subtopic(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="subtopics")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ["topic", "name"]
        ordering = ["order"]

    def __str__(self):
        return f"{self.topic.name} - {self.name}"


class ProblemType(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="problem_types")
    subtopic = models.ForeignKey(Subtopic, on_delete=models.CASCADE, null=True, blank=True, related_name="problem_types")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keywords = models.JSONField(default=list, blank=True)
    solving_strategy = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["topic", "name"]
        ordering = ["name"]

    def __str__(self):
        return f"{self.topic.name} - {self.name}"


class Formula(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="formulas")
    problem_type = models.ForeignKey(ProblemType, on_delete=models.CASCADE, null=True, blank=True, related_name="formulas")
    name = models.CharField(max_length=200)
    formula_latex = models.TextField()
    description = models.TextField(blank=True)
    variables = models.JSONField(default=list, blank=True)
    example_usage = models.TextField(blank=True)

    class Meta:
        ordering = ["topic__name", "name"]

    def __str__(self):
        return self.name
