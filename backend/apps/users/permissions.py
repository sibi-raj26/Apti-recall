from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = getattr(obj, "user", None)
        if user is None:
            return False
        return user.id == request.user.id


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff
