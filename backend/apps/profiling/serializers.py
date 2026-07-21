from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import (
    Category,
    GuardianContact,
    InterviewAnswer,
    StudentCategory,
    StudentGoal,
    StudentInterview,
    StudentProfile,
)


User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id", "code", "title", "description", "kind", "subject_slug",
            "color", "is_active", "order",
        ]


class StudentCategorySerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source="category", read_only=True)

    class Meta:
        model = StudentCategory
        fields = [
            "id", "profile", "category", "category_detail", "source",
            "confidence", "note", "is_active", "created_at",
        ]
        read_only_fields = ["created_at"]


class GuardianContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuardianContact
        fields = [
            "id", "profile", "full_name", "relationship", "phone", "email",
            "workplace", "is_primary",
        ]


class StudentGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentGoal
        fields = [
            "id", "profile", "goal_type", "title", "description", "current_value",
            "target_value", "target_score", "target_date", "priority", "is_primary",
            "is_active", "created_at",
        ]
        read_only_fields = ["created_at"]


class InterviewAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewAnswer
        fields = [
            "id", "question_key", "question_text", "answer_text", "score", "order",
        ]


class StudentInterviewSerializer(serializers.ModelSerializer):
    answers = InterviewAnswerSerializer(many=True, required=False)

    class Meta:
        model = StudentInterview
        fields = [
            "id", "profile", "interviewer", "status", "strengths", "weaknesses",
            "interests", "main_problem", "motivation_level", "independence_level",
            "parent_support_level", "admin_summary", "recommendation", "next_step",
            "answers", "started_at", "completed_at",
        ]
        read_only_fields = ["interviewer", "started_at", "completed_at"]

    @transaction.atomic
    def create(self, validated_data):
        answers = validated_data.pop("answers", [])
        interview = StudentInterview.objects.create(
            interviewer=self.context["request"].user,
            **validated_data,
        )
        InterviewAnswer.objects.bulk_create([
            InterviewAnswer(interview=interview, **answer) for answer in answers
        ])
        interview.profile.status = StudentProfile.Status.INTERVIEW_DRAFT
        interview.profile.save(update_fields=["status", "updated_at"])
        return interview

    @transaction.atomic
    def update(self, instance, validated_data):
        answers = validated_data.pop("answers", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if answers is not None:
            for answer in answers:
                InterviewAnswer.objects.update_or_create(
                    interview=instance,
                    question_key=answer["question_key"],
                    defaults=answer,
                )
        return instance


class StudentProfileSerializer(serializers.ModelSerializer):
    student = serializers.SerializerMethodField()
    guardian_contacts = GuardianContactSerializer(many=True, read_only=True)
    goals = StudentGoalSerializer(many=True, read_only=True)
    category_links = StudentCategorySerializer(many=True, read_only=True)
    interviews = StudentInterviewSerializer(many=True, read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id", "student", "admission_code", "birth_date", "school_name", "grade",
            "region", "district", "weekly_study_hours", "learning_style",
            "internet_access", "device_access", "assigned_admin", "assigned_teacher",
            "status", "guardian_contacts", "goals", "category_links", "interviews",
            "created_at", "updated_at",
        ]
        read_only_fields = ["admission_code", "assigned_admin", "created_at", "updated_at"]

    def get_student(self, obj):
        return {
            "id": obj.student_id,
            "username": obj.student.username,
            "full_name": obj.student.full_name,
            "email": obj.student.email,
            "phone": obj.student.phone,
        }


class StudentOnboardingSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=180)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    school_name = serializers.CharField(required=False, allow_blank=True)
    grade = serializers.IntegerField(min_value=1, max_value=11)
    region = serializers.CharField(required=False, allow_blank=True)
    district = serializers.CharField(required=False, allow_blank=True)
    weekly_study_hours = serializers.IntegerField(min_value=1, max_value=50)
    guardian_name = serializers.CharField(max_length=180)
    guardian_phone = serializers.CharField(max_length=30)
    guardian_relationship = serializers.CharField(max_length=50, default="Ota-ona")

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Bu login bilan foydalanuvchi mavjud.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        guardian_name = validated_data.pop("guardian_name")
        guardian_phone = validated_data.pop("guardian_phone")
        guardian_relationship = validated_data.pop("guardian_relationship", "Ota-ona")
        password = validated_data.pop("password")
        user_fields = {
            "username": validated_data.pop("username"),
            "full_name": validated_data.pop("full_name"),
            "phone": validated_data.pop("phone", ""),
            "email": validated_data.pop("email", ""),
            "role": User.Role.STUDENT,
        }
        user = User.objects.create_user(password=password, **user_fields)
        profile = StudentProfile.objects.create(
            student=user,
            assigned_admin=self.context["request"].user,
            **validated_data,
        )
        GuardianContact.objects.create(
            profile=profile,
            full_name=guardian_name,
            phone=guardian_phone,
            relationship=guardian_relationship,
            is_primary=True,
        )
        return profile

    def to_representation(self, instance):
        return StudentProfileSerializer(instance, context=self.context).data
