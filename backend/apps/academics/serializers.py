from django.db import transaction
from rest_framework import serializers

from apps.accounts.models import Classroom

from .models import Exam, ExamQuestion, ExamSubjectWeight, Question, QuestionOption, Skill, Subject, Topic


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "slug", "title", "color", "order", "is_active"]


class TopicSerializer(serializers.ModelSerializer):
    subject_title = serializers.CharField(source="subject.title", read_only=True)
    prerequisite_titles = serializers.SlugRelatedField(source="prerequisites", many=True, read_only=True, slug_field="title")

    class Meta:
        model = Topic
        fields = ["id", "subject", "subject_title", "parent", "code", "title", "description", "healthy_threshold", "prerequisites", "prerequisite_titles", "order"]


class SkillSerializer(serializers.ModelSerializer):
    subject_title = serializers.CharField(source="subject.title", read_only=True)

    class Meta:
        model = Skill
        fields = ["id", "subject", "subject_title", "slug", "title", "description", "order"]


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ["id", "label", "text", "is_correct", "order"]
        extra_kwargs = {"is_correct": {"write_only": True}}


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True)
    subject_title = serializers.CharField(source="subject.title", read_only=True)
    topic_title = serializers.CharField(source="topic.title", read_only=True)
    skill_details = SkillSerializer(source="skills", many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "code", "subject", "subject_title", "topic", "topic_title", "skills", "skill_details", "prompt", "explanation", "difficulty", "default_points", "image_url", "is_active", "options", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate_options(self, options):
        if len(options) < 2:
            raise serializers.ValidationError("Kamida ikkita javob varianti kerak.")
        if sum(bool(item.get("is_correct")) for item in options) != 1:
            raise serializers.ValidationError("Aynan bitta to‘g‘ri javob belgilang.")
        return options

    @transaction.atomic
    def create(self, validated_data):
        options = validated_data.pop("options")
        skills = validated_data.pop("skills", [])
        question = Question.objects.create(created_by=self.context["request"].user, **validated_data)
        question.skills.set(skills)
        QuestionOption.objects.bulk_create([QuestionOption(question=question, **option) for option in options])
        return question

    @transaction.atomic
    def update(self, instance, validated_data):
        options = validated_data.pop("options", None)
        skills = validated_data.pop("skills", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if skills is not None:
            instance.skills.set(skills)
        if options is not None:
            instance.options.all().delete()
            QuestionOption.objects.bulk_create([QuestionOption(question=instance, **option) for option in options])
        return instance


class ExamSubjectWeightSerializer(serializers.ModelSerializer):
    subject_title = serializers.CharField(source="subject.title", read_only=True)

    class Meta:
        model = ExamSubjectWeight
        fields = ["id", "subject", "subject_title", "weight_percent", "max_score"]


class ExamQuestionSerializer(serializers.ModelSerializer):
    question_detail = QuestionSerializer(source="question", read_only=True)

    class Meta:
        model = ExamQuestion
        fields = ["id", "question", "question_detail", "points", "order"]


class ExamSerializer(serializers.ModelSerializer):
    subject_weights = ExamSubjectWeightSerializer(many=True)
    exam_questions = ExamQuestionSerializer(many=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    target_classroom_names = serializers.SlugRelatedField(source="target_classrooms", many=True, read_only=True, slug_field="name")

    class Meta:
        model = Exam
        fields = ["id", "title", "grade", "description", "duration_minutes", "max_score", "readiness_threshold", "minimum_subject_score", "starts_at", "ends_at", "status", "target_classrooms", "target_classroom_names", "subject_weights", "exam_questions", "created_by", "created_by_name", "created_at", "updated_at"]
        read_only_fields = ["created_by", "created_at", "updated_at"]

    def validate_subject_weights(self, weights):
        total = sum(item["weight_percent"] for item in weights)
        if total != 100:
            raise serializers.ValidationError(f"Fan og‘irliklari jami 100 bo‘lishi kerak. Hozir: {total}.")
        if any(item["max_score"] != 100 for item in weights):
            raise serializers.ValidationError("Har bir fan natijasi 100 ballik shkala bilan saqlanishi kerak.")
        return weights

    @transaction.atomic
    def create(self, validated_data):
        weights = validated_data.pop("subject_weights", [])
        questions = validated_data.pop("exam_questions", [])
        target_classrooms = validated_data.pop("target_classrooms", [])
        exam = Exam.objects.create(created_by=self.context["request"].user, **validated_data)
        exam.target_classrooms.set(target_classrooms)
        ExamSubjectWeight.objects.bulk_create([ExamSubjectWeight(exam=exam, **item) for item in weights])
        ExamQuestion.objects.bulk_create([ExamQuestion(exam=exam, **item) for item in questions])
        return exam

    @transaction.atomic
    def update(self, instance, validated_data):
        weights = validated_data.pop("subject_weights", None)
        questions = validated_data.pop("exam_questions", None)
        target_classrooms = validated_data.pop("target_classrooms", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if target_classrooms is not None:
            instance.target_classrooms.set(target_classrooms)
        if weights is not None:
            instance.subject_weights.all().delete()
            ExamSubjectWeight.objects.bulk_create([ExamSubjectWeight(exam=instance, **item) for item in weights])
        if questions is not None:
            instance.exam_questions.all().delete()
            ExamQuestion.objects.bulk_create([ExamQuestion(exam=instance, **item) for item in questions])
        return instance
