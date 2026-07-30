from collections.abc import Iterable

from django.contrib.auth import get_user_model

from .models import Notification


User = get_user_model()


def notify_users(
    users: Iterable,
    *,
    kind: str,
    title: str,
    message: str = "",
    action_path: str = "",
    metadata: dict | None = None,
) -> list[Notification]:
    recipients = {}
    for user in users:
        if user and getattr(user, "is_active", False):
            recipients[user.id] = user
    return Notification.objects.bulk_create([
        Notification(
            recipient=user,
            kind=kind,
            title=title,
            message=message,
            action_path=action_path,
            metadata=metadata or {},
        )
        for user in recipients.values()
    ])


def family_users(student, *, include_student=True):
    users = []
    if include_student:
        users.append(student)
    users.extend(link.parent for link in student.parent_links.select_related("parent"))
    return users
