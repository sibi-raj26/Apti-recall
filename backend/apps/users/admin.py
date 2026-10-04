from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "username", "is_staff", "is_active", "level", "streak_days", "last_active")
    list_filter = ("is_staff", "is_active", "level", "date_joined")
    search_fields = ("email", "username", "phone")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("username", "phone", "avatar", "level", "streak_days", "last_active")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "username", "password1", "password2")}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "total_questions_attempted", "total_questions_solved", "overall_accuracy", "preferred_language")
    search_fields = ("user__email", "user__username", "preferred_language")
    list_filter = ("preferred_language",)
