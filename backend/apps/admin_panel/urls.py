from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.AdminDashboardView.as_view(), name="admin-dashboard"),
    path("topics/", views.AdminTopicListView.as_view(), name="admin-topic-list"),
    path("topics/<int:pk>/", views.AdminTopicDetailView.as_view(), name="admin-topic-detail"),
    path("questions/", views.AdminQuestionListView.as_view(), name="admin-question-list"),
    path("questions/<int:pk>/", views.AdminQuestionDetailView.as_view(), name="admin-question-detail"),
    path("questions/bulk-import/", views.AdminBulkImportView.as_view(), name="admin-question-bulk-import"),
    path("users/", views.AdminUserListView.as_view(), name="admin-user-list"),
    path("performance/", views.AdminPerformanceView.as_view(), name="admin-performance"),
]
