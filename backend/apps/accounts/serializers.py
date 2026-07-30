from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework import serializers

from .models import Classroom, ClassroomStudent, ParentStudent


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "password", "full_name", "email", "phone", "role", "avatar_url", "is_active", "date_joined"]
        read_only_fields = ["date_joined"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        user.set_password(password or get_random_string(20))
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class ClassroomStudentSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source="student", read_only=True)

    class Meta:
        model = ClassroomStudent
        fields = ["id", "student", "student_detail", "joined_at"]


class ClassroomSerializer(serializers.ModelSerializer):
    teacher_detail = UserSerializer(source="teacher", read_only=True)
    enrollments = ClassroomStudentSerializer(many=True, read_only=True)
    student_count = serializers.IntegerField(source="students.count", read_only=True)

    class Meta:
        model = Classroom
        fields = ["id", "name", "grade", "program", "teacher", "teacher_detail", "is_active", "student_count", "enrollments", "created_at"]
        read_only_fields = ["created_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or user.is_superuser or user.role in {User.Role.ADMIN, User.Role.TEACHER}:
            return data
        allowed_ids = {user.id}
        if user.role == User.Role.PARENT:
            allowed_ids = set(user.children_links.values_list("student_id", flat=True))
        data["enrollments"] = [
            enrollment
            for enrollment in data["enrollments"]
            if enrollment["student"] in allowed_ids
        ]
        data["student_count"] = len(data["enrollments"])
        return data


class ParentStudentSerializer(serializers.ModelSerializer):
    parent_detail = UserSerializer(source="parent", read_only=True)
    student_detail = UserSerializer(source="student", read_only=True)

    class Meta:
        model = ParentStudent
        fields = ["id", "parent", "parent_detail", "student", "student_detail", "relationship", "created_at"]
        read_only_fields = ["created_at"]

    def validate(self, attrs):
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        student = attrs.get("student", getattr(self.instance, "student", None))
        if parent and parent.role != User.Role.PARENT:
            raise serializers.ValidationError({"parent": "Ota-ona rolidagi foydalanuvchini tanlang."})
        if student and student.role != User.Role.STUDENT:
            raise serializers.ValidationError({"student": "O‘quvchi rolidagi foydalanuvchini tanlang."})
        return attrs
