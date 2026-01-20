from rest_framework.permissions import BasePermission
from accounts.models import User


class IsDeveloper(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.DEVELOPER
        )


class IsMentor(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.MENTOR
            and request.user.is_approved
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_staff
        )
