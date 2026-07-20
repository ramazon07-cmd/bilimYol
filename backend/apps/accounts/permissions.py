from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(request.user.is_authenticated and (request.user.role == "admin" or request.user.is_superuser))


class IsTeacherOrAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(request.user.is_authenticated and (request.user.role in {"teacher", "admin"} or request.user.is_superuser))


class ReadOnlyOrAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return bool(request.user.is_authenticated)
        return bool(request.user.is_authenticated and (request.user.role == "admin" or request.user.is_superuser))
