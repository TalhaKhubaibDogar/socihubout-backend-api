from rest_framework import permissions


class IsHostUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return getattr(request.user, 'role', None) == 1


class IsNormalUser(permissions.BasePermission):
    message = "Host is not allowed"

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'role', None) == 2
