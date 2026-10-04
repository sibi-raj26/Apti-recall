import django_filters
from django.db.models import Q
from .models import Question


class QuestionFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search", label="Search")
    topic = django_filters.NumberFilter(field_name="topic__id")
    subtopic = django_filters.NumberFilter(field_name="subtopic__id")
    problem_type = django_filters.NumberFilter(field_name="problem_type__id")
    difficulty = django_filters.ChoiceFilter(choices=Question.DIFFICULTY_CHOICES)
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Question
        fields = ["topic", "subtopic", "problem_type", "difficulty", "is_active"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(question_text__icontains=value)
            | Q(correct_answer__icontains=value)
            | Q(tags__icontains=value)
            | Q(topic__name__icontains=value)
            | Q(problem_type__name__icontains=value)
        )
