from django.conf import settings
from rest_framework.permissions import BasePermission


class ProductionAdminOrDebugAccess(BasePermission):
    """Keep API documentation open locally and admin-only in production."""

    def has_permission(self, request, view) -> bool:
        if settings.DEBUG:
            return True
        user = request.user
        return bool(
            user.is_authenticated
            and (
                user.is_superuser
                or user.is_staff
                or getattr(user, "role", None) == "admin"
            )
        )
