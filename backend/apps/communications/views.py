from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import decorators, response, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .models import Conversation, Message, Notification
from .serializers import ConversationSerializer, MessageSerializer, NotificationSerializer
from .services import notify_users


User = get_user_model()


def conversation_queryset_for(user):
    queryset = Conversation.objects.select_related(
        "student", "parent", "teacher", "created_by",
    ).prefetch_related("messages__sender")
    if user.is_superuser or user.role == User.Role.ADMIN:
        return queryset
    if user.role == User.Role.PARENT:
        return queryset.filter(parent=user)
    if user.role == User.Role.TEACHER:
        return queryset.filter(teacher=user)
    if user.role == User.Role.STUDENT:
        return queryset.filter(student=user)
    return queryset.none()


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["kind", "is_read"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @decorators.action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
        return response.Response(self.get_serializer(notification).data)

    @decorators.action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        now = timezone.now()
        self.get_queryset().filter(is_read=False).update(is_read=True, read_at=now)
        return response.Response({"updated": True}, status=status.HTTP_200_OK)


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]
    filterset_fields = ["kind", "student", "parent", "teacher"]

    def get_queryset(self):
        return conversation_queryset_for(self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        student = serializer.validated_data["student"]
        parent = serializer.validated_data["parent"]
        teacher = serializer.validated_data.get("teacher")
        allowed = user.is_superuser or user.role == User.Role.ADMIN
        if user.role == User.Role.PARENT:
            allowed = parent == user and user.children_links.filter(student=student).exists()
        elif user.role == User.Role.TEACHER:
            allowed = teacher == user and student.classrooms.filter(teacher=user).exists()
        if not allowed:
            raise PermissionDenied("Bu suhbatni yaratish huquqiga ega emassiz.")
        serializer.save(created_by=user)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]
    filterset_fields = ["conversation"]

    def get_queryset(self):
        return Message.objects.filter(
            conversation__in=conversation_queryset_for(self.request.user),
        ).select_related("sender", "conversation")

    def perform_create(self, serializer):
        conversation = serializer.validated_data["conversation"]
        if not conversation_queryset_for(self.request.user).filter(id=conversation.id).exists():
            raise PermissionDenied("Bu suhbatga xabar yoza olmaysiz.")
        message = serializer.save(sender=self.request.user)
        Conversation.objects.filter(id=conversation.id).update(updated_at=timezone.now())
        recipients = [conversation.parent, conversation.student]
        if conversation.teacher:
            recipients.append(conversation.teacher)
        if conversation.kind == Conversation.Kind.ACADEMIC:
            recipients.extend(User.objects.filter(role=User.Role.ADMIN, is_active=True))
        notify_users(
            [user for user in recipients if user.id != self.request.user.id],
            kind=Notification.Kind.MESSAGE,
            title="Yangi xabar",
            message=message.body[:180],
            action_path="messages",
            metadata={"conversation_id": conversation.id},
        )
