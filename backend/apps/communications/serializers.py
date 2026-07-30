from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import Conversation, Message, Notification


User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id", "kind", "title", "message", "action_path", "metadata",
            "is_read", "read_at", "created_at",
        ]
        read_only_fields = [
            "kind", "title", "message", "action_path", "metadata", "read_at", "created_at",
        ]


class MessageSerializer(serializers.ModelSerializer):
    sender_detail = UserSerializer(source="sender", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "conversation", "sender", "sender_detail", "body", "created_at"]
        read_only_fields = ["sender", "sender_detail", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source="student", read_only=True)
    parent_detail = UserSerializer(source="parent", read_only=True)
    teacher_detail = UserSerializer(source="teacher", read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id", "kind", "title", "student", "student_detail", "parent",
            "parent_detail", "teacher", "teacher_detail", "messages",
            "last_message", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_last_message(self, obj):
        message = obj.messages.last()
        return MessageSerializer(message, context=self.context).data if message else None

    def validate(self, attrs):
        student = attrs.get("student", getattr(self.instance, "student", None))
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        teacher = attrs.get("teacher", getattr(self.instance, "teacher", None))
        kind = attrs.get("kind", getattr(self.instance, "kind", None))
        if student and student.role != User.Role.STUDENT:
            raise serializers.ValidationError({"student": "O‘quvchini tanlang."})
        if parent and parent.role != User.Role.PARENT:
            raise serializers.ValidationError({"parent": "Ota-onani tanlang."})
        if student and parent and not parent.children_links.filter(student=student).exists():
            raise serializers.ValidationError({"parent": "Bu ota-ona tanlangan o‘quvchiga biriktirilmagan."})
        if kind == Conversation.Kind.TEACHER:
            if not teacher or teacher.role != User.Role.TEACHER:
                raise serializers.ValidationError({"teacher": "O‘qituvchini tanlang."})
            if student and not student.classrooms.filter(teacher=teacher).exists():
                raise serializers.ValidationError({"teacher": "Bu o‘qituvchi o‘quvchining sinfiga biriktirilmagan."})
        if kind == Conversation.Kind.ACADEMIC:
            attrs["teacher"] = None
        return attrs
