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

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False) and (
            getattr(user, "is_superuser", False)
            or getattr(user, "role", None) in {"admin", "teacher"}
        ):
            fields["is_correct"].write_only = False
        return fields


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True)
    subject_title = serializers.CharField(source="subject.title", read_only=True)
    topic_title = serializers.CharField(source="topic.title", read_only=True)
    skill_details = SkillSerializer(source="skills", many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "code", "subject", "subject_title", "topic", "topic_title", "skills", "skill_details", "context", "prompt", "explanation", "difficulty", "min_grade", "max_grade", "default_points", "image_url", "is_active", "options", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not getattr(user, "is_authenticated", False) or (
            not getattr(user, "is_superuser", False)
            and getattr(user, "role", None) not in {"admin", "teacher"}
        ):
            fields.pop("explanation", None)
        return fields

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
        options_changed = False
        if options is not None:
            current_options = [
                {
                    "label": option.label,
                    "text": option.text,
                    "is_correct": option.is_correct,
                    "order": option.order,
                }
                for option in instance.options.all()
            ]
            incoming_options = [
                {
                    "label": option["label"],
                    "text": option["text"],
                    "is_correct": bool(option.get("is_correct", False)),
                    "order": option.get("order", 0),
                }
                for option in options
            ]
            options_changed = current_options != incoming_options
            if options_changed and instance.options.filter(student_selections__isnull=False).exists():
                raise serializers.ValidationError({
                    "options": "Javob berilgan savol variantlarini almashtirib bo‘lmaydi. Savolni arxivlab, yangisini yarating."
                })
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if skills is not None:
            instance.skills.set(skills)
        if options is not None and options_changed:
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
    recommended_category_names = serializers.SlugRelatedField(source="recommended_categories", many=True, read_only=True, slug_field="title")

    class Meta:
        model = Exam
        fields = ["id", "title", "grade", "purpose", "description", "duration_minutes", "max_score", "readiness_threshold", "minimum_subject_score", "starts_at", "ends_at", "status", "target_classrooms", "target_classroom_names", "recommended_categories", "recommended_category_names", "subject_weights", "exam_questions", "created_by", "created_by_name", "created_at", "updated_at"]
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
        recommended_categories = validated_data.pop("recommended_categories", [])
        exam = Exam.objects.create(created_by=self.context["request"].user, **validated_data)
        exam.target_classrooms.set(target_classrooms)
        exam.recommended_categories.set(recommended_categories)
        ExamSubjectWeight.objects.bulk_create([ExamSubjectWeight(exam=exam, **item) for item in weights])
        ExamQuestion.objects.bulk_create([ExamQuestion(exam=exam, **item) for item in questions])
        return exam

    @transaction.atomic
    def update(self, instance, validated_data):
        weights = validated_data.pop("subject_weights", None)
        questions = validated_data.pop("exam_questions", None)
        target_classrooms = validated_data.pop("target_classrooms", None)
        recommended_categories = validated_data.pop("recommended_categories", None)
        questions_changed = False
        if questions is not None:
            current_questions = [
                {
                    "question": item.question_id,
                    "points": item.points,
                    "order": item.order,
                }
                for item in instance.exam_questions.all()
            ]
            incoming_questions = [
                {
                    "question": item["question"].id,
                    "points": item.get("points", 1),
                    "order": item.get("order", 0),
                }
                for item in questions
            ]
            questions_changed = current_questions != incoming_questions
            if (
                questions_changed
                and instance.exam_questions.filter(student_answers__isnull=False).exists()
            ):
                raise serializers.ValidationError({
                    "exam_questions": "Javoblar mavjud test tarkibini almashtirib bo‘lmaydi. Testni arxivlab, yangisini yarating."
                })
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if target_classrooms is not None:
            instance.target_classrooms.set(target_classrooms)
        if recommended_categories is not None:
            instance.recommended_categories.set(recommended_categories)
        if weights is not None:
            instance.subject_weights.all().delete()
            ExamSubjectWeight.objects.bulk_create([ExamSubjectWeight(exam=instance, **item) for item in weights])
        if questions is not None and questions_changed:
            instance.exam_questions.all().delete()
            ExamQuestion.objects.bulk_create([ExamQuestion(exam=instance, **item) for item in questions])
        return instance
