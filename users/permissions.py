from rest_framework import permissions


class IsHostUser(permissions.BasePermission):
    """
        Host Specfic Permission
    """
    message = "User is not allowed"

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return getattr(request.user, 'role', None) == 1


class IsNormalUser(permissions.BasePermission):
    """
        User Specfic Permissions
    """
    message = "Host is not allowed"

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'role', None) == 2
