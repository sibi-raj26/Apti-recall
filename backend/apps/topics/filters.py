import django_filters
from django.db.models import Q
from .models import Topic


class TopicFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search", label="Search")

    class Meta:
        model = Topic
        fields = ["is_active", "order"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value) | Q(slug__icontains=value))
