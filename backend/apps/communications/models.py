from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Kind(models.TextChoices):
        ASSIGNMENT = "assignment", "Yangi test"
        RESULT = "result", "Yangi natija"
        ROADMAP = "roadmap", "Roadmap"
        UNIVERSITY = "university", "Universitet maqsadi"
        CERTIFICATE = "certificate", "Sertifikat"
        MESSAGE = "message", "Xabar"
        SYSTEM = "system", "Tizim"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(max_length=24, choices=Kind.choices, default=Kind.SYSTEM, db_index=True)
    title = models.CharField(max_length=180)
    message = models.TextField(blank=True)
    action_path = models.CharField(max_length=220, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.recipient} · {self.title}"


class Conversation(models.Model):
    class Kind(models.TextChoices):
        TEACHER = "teacher", "O‘qituvchi"
        ACADEMIC = "academic", "Akademik bo‘lim"

    kind = models.CharField(max_length=16, choices=Kind.choices)
    title = models.CharField(max_length=180)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_conversations",
        limit_choices_to={"role": "student"},
    )
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parent_conversations",
        limit_choices_to={"role": "parent"},
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teacher_conversations",
        limit_choices_to={"role": "teacher"},
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "parent", "kind"],
                name="unique_family_conversation_kind",
            )
        ]

    def __str__(self) -> str:
        return f"{self.title} · {self.student}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    body = models.TextField(max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.sender} · {self.body[:40]}"
